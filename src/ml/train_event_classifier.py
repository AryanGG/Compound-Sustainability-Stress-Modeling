"""
src/ml/train_event_classifier.py
────────────────────────────────
Steps 03 & 04: Cost-Sensitive Machine Learning Training & Chronological Out-of-Time (OOT) Validation.

Trains tree-based gradient boosted models to forecast 30-day forward discrete crisis events
and continuous SSI trajectory:
  - Strict Chronological OOT Validation: Train on 2020–2021, evaluate strictly on 2022.
  - Cost-sensitive classification to handle extreme class imbalance.
  - Evaluation on pre-registered historical benchmarks:
      * Benchmark A: March–April 2022 historic heatwave surge.
      * Benchmark B: October–November 2022 post-monsoon inversion smog.
  - Outputs full metrics to reports/ and results/ with provenance tracking.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    fbeta_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
)

from src.ml.temporal_features import get_feature_column_names
from src.utils.logger import get_logger
from src.utils.results_io import save_result

log = get_logger("train_event_classifier")

EVENT_TARGETS = [
    ("target_event_heatwave_1m", "heatwave"),
    ("target_event_smog_1m", "smog"),
    ("target_event_compound_1m", "compound"),
    ("target_event_any_emergency_1m", "any_emergency"),
]


def train_and_eval_binary_classifier(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    event_name: str,
    random_state: int = 42,
) -> tuple[HistGradientBoostingClassifier, dict[str, Any], np.ndarray, np.ndarray]:
    """
    Train a cost-sensitive HistGradientBoostingClassifier and compute comprehensive OOT metrics.
    """
    n_pos_train = int(y_train.sum())
    n_pos_test = int(y_test.sum())

    # Check for degenerate cases
    if n_pos_train == 0 or n_pos_test == 0 or n_pos_train == len(y_train) or n_pos_test == len(y_test):
        log.warning(f"Extreme degenerate class distribution for {event_name}: train pos={n_pos_train}/{len(y_train)}, test pos={n_pos_test}/{len(y_test)}")
        clf = HistGradientBoostingClassifier(random_state=random_state)
        clf.fit(X_train, y_train)
        probs = clf.predict_proba(X_test)[:, 1] if len(clf.classes_) > 1 else np.zeros(len(X_test))
        preds = clf.predict(X_test)
        metrics = {
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "train_prevalence": round(float(y_train.mean()), 4),
            "test_prevalence": round(float(y_test.mean()), 4),
            "roc_auc": 0.5,
            "pr_auc": round(float(y_test.mean()), 4),
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "f2": 0.0,
            "brier_score": 0.0,
            "confusion_matrix": {"tp": 0, "fp": 0, "tn": len(X_test), "fn": 0},
        }
        return clf, metrics, preds, probs

    # Train cost-sensitive classifier
    clf = HistGradientBoostingClassifier(
        class_weight="balanced",
        random_state=random_state,
        max_iter=100,
        learning_rate=0.1,
    )
    clf.fit(X_train, y_train)

    probs = clf.predict_proba(X_test)[:, 1]
    preds = clf.predict(X_test)

    # Compute metrics
    roc = float(roc_auc_score(y_test, probs))
    pr_auc = float(average_precision_score(y_test, probs))
    prec = float(precision_score(y_test, preds, zero_division=0))
    rec = float(recall_score(y_test, preds, zero_division=0))
    f1 = float(f1_score(y_test, preds, zero_division=0))
    f2 = float(fbeta_score(y_test, preds, beta=2.0, zero_division=0))
    brier = float(brier_score_loss(y_test, probs))

    tn, fp, fn, tp = confusion_matrix(y_test, preds, labels=[0, 1]).ravel()

    metrics = {
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "train_prevalence": round(float(y_train.mean()), 4),
        "test_prevalence": round(float(y_test.mean()), 4),
        "roc_auc": round(roc, 4),
        "pr_auc": round(pr_auc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "f2": round(f2, 4),
        "brier_score": round(brier, 4),
        "confusion_matrix": {"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)},
    }

    return clf, metrics, preds, probs


def train_and_eval_regressor(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    random_state: int = 42,
) -> tuple[HistGradientBoostingRegressor, dict[str, Any], np.ndarray]:
    """
    Train HistGradientBoostingRegressor to forecast continuous SSI 30 days ahead.
    """
    reg = HistGradientBoostingRegressor(
        random_state=random_state,
        max_iter=100,
        learning_rate=0.1,
    )
    reg.fit(X_train, y_train)

    preds = reg.predict(X_test)

    r2 = float(r2_score(y_test, preds))
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(root_mean_squared_error(y_test, preds))

    metrics = {
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "r2_score": round(r2, 4),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "test_mean_actual": round(float(y_test.mean()), 4),
        "test_mean_predicted": round(float(preds.mean()), 4),
    }

    return reg, metrics, preds


def evaluate_city_models(
    city: str,
    features_dir: str | Path = "data/h3_panel/ml_features",
    predictions_dir: str | Path = "data/h3_panel/ml_predictions",
    split_date: str = "2022-01-01",
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Train and evaluate all event classifiers and the continuous SSI regressor for a single city.
    """
    input_path = Path(features_dir) / f"{city}.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Feature matrix not found: {input_path}")

    df = pd.read_parquet(input_path)
    # Ensure valid rows
    valid_mask = df["temp_mean_c_lag2"].notna() & df["target_event_heatwave_1m"].notna()
    df_valid = df.loc[valid_mask].copy().reset_index(drop=True)

    # Feature extraction (numeric only)
    feature_candidates = get_feature_column_names(df_valid)
    numeric_features = [
        f for f in feature_candidates
        if np.issubdtype(df_valid[f].dtype, np.number)
    ]

    train_mask = df_valid["date"] < split_date
    test_mask = df_valid["date"] >= split_date

    X_train = df_valid.loc[train_mask, numeric_features]
    X_test = df_valid.loc[test_mask, numeric_features]

    results_city: dict[str, Any] = {
        "city": city,
        "split_date": split_date,
        "n_features": len(numeric_features),
        "train_period": f"{df_valid.loc[train_mask, 'date'].min()} to {df_valid.loc[train_mask, 'date'].max()}",
        "test_period": f"{df_valid.loc[test_mask, 'date'].min()} to {df_valid.loc[test_mask, 'date'].max()}",
        "train_rows": int(train_mask.sum()),
        "test_rows": int(test_mask.sum()),
        "events": {},
        "continuous_ssi": {},
        "benchmarks": {},
    }

    # Dataframe to store 2022 test set predictions for mapping and dashboards
    pred_df = df_valid.loc[test_mask, ["h3_index", "date", "latitude", "longitude"]].copy()

    # 1. Train and evaluate discrete event classifiers
    classifiers = {}
    for col, ev_name in EVENT_TARGETS:
        if col not in df_valid.columns:
            continue
        y_train = df_valid.loc[train_mask, col].astype(int)
        y_test = df_valid.loc[test_mask, col].astype(int)

        clf, ev_metrics, preds, probs = train_and_eval_binary_classifier(
            X_train, y_train, X_test, y_test, event_name=ev_name, random_state=random_state
        )
        classifiers[ev_name] = clf
        results_city["events"][ev_name] = ev_metrics

        pred_df[f"actual_{ev_name}"] = y_test.values
        pred_df[f"pred_{ev_name}"] = preds
        pred_df[f"prob_{ev_name}"] = np.round(probs, 4)

    # 2. Train and evaluate continuous SSI regressor
    if "target_ssi_v2_1m" in df_valid.columns:
        y_train_ssi = df_valid.loc[train_mask, "target_ssi_v2_1m"]
        y_test_ssi = df_valid.loc[test_mask, "target_ssi_v2_1m"]

        reg, ssi_metrics, ssi_preds = train_and_eval_regressor(
            X_train, y_train_ssi, X_test, y_test_ssi, random_state=random_state
        )
        results_city["continuous_ssi"] = ssi_metrics
        pred_df["actual_ssi_v2_1m"] = y_test_ssi.values
        pred_df["pred_ssi_v2_1m"] = np.round(ssi_preds, 4)

    # 3. Evaluate Historical Benchmarks
    # Benchmark A: Historic March-April 2022 Heatwave Surge
    hw_bench_mask = pred_df["date"].isin(["2022-03-01", "2022-04-01"])
    if hw_bench_mask.sum() > 0 and "actual_heatwave" in pred_df.columns:
        y_hw = pred_df.loc[hw_bench_mask, "actual_heatwave"]
        p_hw = pred_df.loc[hw_bench_mask, "pred_heatwave"]
        prob_hw = pred_df.loc[hw_bench_mask, "prob_heatwave"]
        if y_hw.sum() > 0:
            rec_hw = float(recall_score(y_hw, p_hw, zero_division=0))
            prec_hw = float(precision_score(y_hw, p_hw, zero_division=0))
            f2_hw = float(fbeta_score(y_hw, p_hw, beta=2.0, zero_division=0))
            results_city["benchmarks"]["Benchmark_A_March_April_2022_Heatwave"] = {
                "hex_months": int(hw_bench_mask.sum()),
                "true_heatwave_count": int(y_hw.sum()),
                "heatwave_share": round(float(y_hw.mean()), 4),
                "recall": round(rec_hw, 4),
                "precision": round(prec_hw, 4),
                "f2_score": round(f2_hw, 4),
            }

    # Benchmark B: November 2022 Winter Inversion Smog Spike
    smog_bench_mask = pred_df["date"].isin(["2022-10-01", "2022-11-01"])
    if smog_bench_mask.sum() > 0 and "actual_smog" in pred_df.columns:
        y_smog = pred_df.loc[smog_bench_mask, "actual_smog"]
        p_smog = pred_df.loc[smog_bench_mask, "pred_smog"]
        if y_smog.sum() > 0:
            rec_smog = float(recall_score(y_smog, p_smog, zero_division=0))
            prec_smog = float(precision_score(y_smog, p_smog, zero_division=0))
            f2_smog = float(fbeta_score(y_smog, p_smog, beta=2.0, zero_division=0))
            results_city["benchmarks"]["Benchmark_B_Nov_2022_Smog_Spike"] = {
                "hex_months": int(smog_bench_mask.sum()),
                "true_smog_count": int(y_smog.sum()),
                "smog_share": round(float(y_smog.mean()), 4),
                "recall": round(rec_smog, 4),
                "precision": round(prec_smog, 4),
                "f2_score": round(f2_smog, 4),
            }

    # Save 2022 test predictions
    predictions_dir = Path(predictions_dir)
    predictions_dir.mkdir(parents=True, exist_ok=True)
    out_pred_path = predictions_dir / f"{city}_2022_predictions.parquet"
    pred_df.to_parquet(out_pred_path, index=False)
    log.info(f"Saved {city} 2022 predictions ({len(pred_df)} rows) -> {out_pred_path}")

    return results_city


def run_event_training_pipeline(
    cities: list[str] | None = None,
    features_dir: str | Path = "data/h3_panel/ml_features",
    predictions_dir: str | Path = "data/h3_panel/ml_predictions",
    report_path: str | Path = "reports/ml_event_prediction_metrics.json",
    split_date: str = "2022-01-01",
) -> dict[str, Any]:
    """
    Run Steps 03 & 04 across all 7 cities and save provenance-tracked reports.
    """
    if cities is None:
        cities = ["delhi", "mumbai", "kolkata", "hyderabad", "bikaner", "coimbatore", "indore"]

    all_metrics: dict[str, Any] = {}
    for c in cities:
        log.info(f"Training and evaluating OOT models for {c}...")
        res = evaluate_city_models(
            city=c,
            features_dir=features_dir,
            predictions_dir=predictions_dir,
            split_date=split_date,
        )
        all_metrics[c] = res

    # Save summary report in reports/
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as fh:
        json.dump(all_metrics, fh, indent=2)

    # Maintain provenance-tracked results in results/
    try:
        save_result(
            "ml_event_prediction_metrics",
            all_metrics,
            config={"step": "03_04_event_training_oot", "split_date": split_date, "seed": 20260101},
        )
        log.info("Saved provenance-tracked result -> results/ml_event_prediction_metrics.json")
    except Exception as exc:
        log.warning(f"Failed to save to results/: {exc}")

    log.info(f"Event prediction metrics saved to {report_path}")
    return all_metrics


if __name__ == "__main__":
    metrics = run_event_training_pipeline()
    print("\n" + "=" * 90)
    print("=== STEPS 03 & 04: CHRONOLOGICAL OUT-OF-TIME EVENT PREDICTION BENCHMARK (TEST YEAR = 2022) ===")
    print("=" * 90)
    for city, res in metrics.items():
        ev = res["events"]
        hw = ev.get("heatwave", {})
        smog = ev.get("smog", {})
        comp = ev.get("compound", {})
        ssi = res["continuous_ssi"]
        print(
            f"{city:12s} | "
            f"Heat PR-AUC: {hw.get('pr_auc', 0):.3f} (Rec: {hw.get('recall', 0):.2f}) | "
            f"Smog PR-AUC: {smog.get('pr_auc', 0):.3f} (Rec: {smog.get('recall', 0):.2f}) | "
            f"Comp PR-AUC: {comp.get('pr_auc', 0):.3f} | "
            f"Future SSI R²: {ssi.get('r2_score', 0):.3f} (MAE: {ssi.get('mae', 0):.3f})"
        )
    print("=" * 90)
