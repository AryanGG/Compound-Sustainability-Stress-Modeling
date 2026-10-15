"""
tests/test_train_event_classifier.py
────────────────────────────────────
Unit tests for Steps 03 & 04: Event Training & Chronological OOT Validation.
"""

import numpy as np
import pandas as pd
import pytest

from src.ml.train_event_classifier import (
    train_and_eval_binary_classifier,
    train_and_eval_regressor,
)


@pytest.fixture
def synthetic_split_data():
    """Synthetic train/test matrices with controlled distribution."""
    np.random.seed(20260101)
    n_train, n_test = 200, 100
    n_features = 10

    X_train = pd.DataFrame(
        np.random.randn(n_train, n_features),
        columns=[f"feat_{i}" for i in range(n_features)],
    )
    # Target correlated with feat_0
    y_train = (X_train["feat_0"] > 0.5).astype(int)

    X_test = pd.DataFrame(
        np.random.randn(n_test, n_features),
        columns=[f"feat_{i}" for i in range(n_features)],
    )
    y_test = (X_test["feat_0"] > 0.5).astype(int)

    return X_train, y_train, X_test, y_test


def test_binary_classifier_training(synthetic_split_data):
    X_train, y_train, X_test, y_test = synthetic_split_data

    clf, metrics, preds, probs = train_and_eval_binary_classifier(
        X_train, y_train, X_test, y_test, event_name="test_heatwave"
    )

    # Check metric keys
    required_keys = [
        "roc_auc", "pr_auc", "precision", "recall", "f1", "f2",
        "brier_score", "confusion_matrix"
    ]
    for k in required_keys:
        assert k in metrics

    # Probabilities in [0, 1]
    assert (probs >= 0.0).all() and (probs <= 1.0).all()

    # Predictions in {0, 1}
    assert set(np.unique(preds)).issubset({0, 1})

    # Confusion matrix sum matches test size
    cm = metrics["confusion_matrix"]
    assert cm["tp"] + cm["fp"] + cm["tn"] + cm["fn"] == len(X_test)


def test_regressor_training(synthetic_split_data):
    X_train, _, X_test, _ = synthetic_split_data

    # Continuous target
    y_train = X_train["feat_0"] * 2.0 + X_train["feat_1"] * 0.5
    y_test = X_test["feat_0"] * 2.0 + X_test["feat_1"] * 0.5

    reg, metrics, preds = train_and_eval_regressor(X_train, y_train, X_test, y_test)

    assert "r2_score" in metrics
    assert "mae" in metrics
    assert "rmse" in metrics
    assert metrics["r2_score"] > 0.50
    assert len(preds) == len(X_test)


def test_degenerate_class_handling(synthetic_split_data):
    X_train, _, X_test, _ = synthetic_split_data
    # 0 positives
    y_train = pd.Series([0] * len(X_train))
    y_test = pd.Series([0] * len(X_test))

    clf, metrics, preds, probs = train_and_eval_binary_classifier(
        X_train, y_train, X_test, y_test, event_name="test_zero"
    )
    assert metrics["recall"] == 0.0
    assert metrics["precision"] == 0.0
