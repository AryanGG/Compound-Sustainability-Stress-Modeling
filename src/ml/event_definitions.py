"""
src/ml/event_definitions.py
───────────────────────────
Step 01: Pre-Registration of Ground-Truth Statutory and Empirical Event Definitions.

Provides mathematical formulations for 4 distinct extreme sustainability events:
  1. Flash Heatwave Shock (Event_Heatwave)
  2. Hazardous Inversion Smog Episode (Event_Smog)
  3. Joint-Tail Compound Crisis (Event_Compound)
  4. Extreme Sustainability Stress Breach (Event_Extreme_SSI)

Supports three evaluation regimes:
  - 'statutory': Pure national statutory limits (IMD heatwave criteria, CPCB PM2.5 > 250).
  - 'relative_tail': Hyperlocal 90th/95th historical percentile per city.
  - 'hybrid': Logical OR of statutory threshold and relative 90th percentile.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

log = get_logger("event_definitions")

# Target Metropolitan Study Areas
CITIES = ["delhi", "mumbai", "kolkata", "hyderabad", "bikaner", "coimbatore", "indore"]

# Statutory Benchmarks
LST_STATUTORY_HEATWAVE_C = 42.0       # IMD severe thermal threshold
HEAT_V2_ALERT_THRESHOLD = 0.85        # Normalized heat index high alert
PM25_STATUTORY_SEVERE_UGM3 = 250.0   # CPCB "Severe" AQI lower boundary
POLLUTION_V2_ALERT_THRESHOLD = 0.85   # Normalized pollution high alert
SSI_EXTREME_THRESHOLD = 0.70          # Standard extreme band threshold



def compute_event_heatwave(
    df: pd.DataFrame,
    lst_col: str = "lst_c",
    heat_idx_col: str = "heat_v2",
    q: float = 0.90,
    statutory_c: float = LST_STATUTORY_HEATWAVE_C,
    mode: Literal["statutory", "relative_tail", "hybrid"] = "hybrid",
) -> pd.Series:
    """
    Compute binary indicator for Flash Heatwave Shock.

    Parameters
    ----------
    df : pd.DataFrame
        Input table containing satellite LST and/or normalized heat index.
    lst_col : str
        Column for MODIS Land Surface Temperature in °C.
    heat_idx_col : str
        Column for normalized v2 heat stress index.
    q : float
        Percentile cutoff for relative tail (default 0.90).
    statutory_c : float
        Absolute temperature threshold in °C (default 42.0).
    mode : 'statutory' | 'relative_tail' | 'hybrid'
        Event definition mode.

    Returns
    -------
    pd.Series
        Binary series (1 for event, 0 otherwise).
    """
    has_lst = lst_col in df.columns
    has_idx = heat_idx_col in df.columns

    if not has_lst and not has_idx:
        raise ValueError(f"Neither '{lst_col}' nor '{heat_idx_col}' found in DataFrame.")

    # Statutory condition: absolute extreme
    statutory_mask = pd.Series(False, index=df.index)
    if has_lst:
        statutory_mask = statutory_mask | (df[lst_col] >= statutory_c)
    if has_idx:
        statutory_mask = statutory_mask | (df[heat_idx_col] >= HEAT_V2_ALERT_THRESHOLD)

    # Relative tail condition: top (1 - q) quantile within local historical sample
    relative_mask = pd.Series(False, index=df.index)
    if has_lst:
        cutoff = df[lst_col].quantile(q)
        relative_mask = relative_mask | (df[lst_col] >= cutoff)
    elif has_idx:
        cutoff = df[heat_idx_col].quantile(q)
        relative_mask = relative_mask | (df[heat_idx_col] >= cutoff)

    if mode == "statutory":
        res = statutory_mask
    elif mode == "relative_tail":
        res = relative_mask
    elif mode == "hybrid":
        res = statutory_mask | relative_mask
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return res.astype(int)


def compute_event_smog(
    df: pd.DataFrame,
    pm25_col: str = "pm25",
    poll_idx_col: str = "pollution_v2",
    q: float = 0.90,
    statutory_ugm3: float = PM25_STATUTORY_SEVERE_UGM3,
    mode: Literal["statutory", "relative_tail", "hybrid"] = "hybrid",
) -> pd.Series:
    """
    Compute binary indicator for Hazardous Inversion Smog Episode.

    Parameters
    ----------
    df : pd.DataFrame
        Input table containing PM2.5 and/or normalized pollution index.
    pm25_col : str
        Column for PM2.5 in µg/m³.
    poll_idx_col : str
        Column for normalized v2 pollution index.
    q : float
        Percentile cutoff for relative tail (default 0.90).
    statutory_ugm3 : float
        CPCB Severe statutory threshold (default 250.0 µg/m³).
    mode : 'statutory' | 'relative_tail' | 'hybrid'
        Event definition mode.

    Returns
    -------
    pd.Series
        Binary series (1 for event, 0 otherwise).
    """
    has_pm = pm25_col in df.columns
    has_idx = poll_idx_col in df.columns

    if not has_pm and not has_idx:
        raise ValueError(f"Neither '{pm25_col}' nor '{poll_idx_col}' found in DataFrame.")

    # Statutory condition: CPCB Severe limit
    statutory_mask = pd.Series(False, index=df.index)
    if has_pm:
        statutory_mask = statutory_mask | (df[pm25_col] >= statutory_ugm3)
    if has_idx:
        statutory_mask = statutory_mask | (df[poll_idx_col] >= POLLUTION_V2_ALERT_THRESHOLD)

    # Relative tail condition: top (1 - q) quantile
    relative_mask = pd.Series(False, index=df.index)
    if has_pm:
        cutoff = df[pm25_col].quantile(q)
        relative_mask = relative_mask | (df[pm25_col] >= cutoff)
    elif has_idx:
        cutoff = df[poll_idx_col].quantile(q)
        relative_mask = relative_mask | (df[poll_idx_col] >= cutoff)

    if mode == "statutory":
        res = statutory_mask
    elif mode == "relative_tail":
        res = relative_mask
    elif mode == "hybrid":
        res = statutory_mask | relative_mask
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return res.astype(int)


def compute_event_compound(
    df: pd.DataFrame,
    omega_col: str = "omega_v2",
) -> pd.Series:
    """
    Compute binary indicator for Joint-Tail Compound Multi-Hazard Crisis.
    Triggers whenever the non-linear joint tail amplifier is activated (omega_v2 > 0).
    """
    if omega_col in df.columns:
        return (df[omega_col] > 0.0).astype(int)
    elif "omega_compound" in df.columns:
        return (df["omega_compound"] > 0.0).astype(int)
    else:
        raise ValueError(f"Neither '{omega_col}' nor 'omega_compound' found in DataFrame.")


def compute_event_extreme_ssi(
    df: pd.DataFrame,
    ssi_band_col: str = "ssi_band_v2",
    ssi_val_col: str = "ssi_v2",
    threshold: float = SSI_EXTREME_THRESHOLD,
) -> pd.Series:
    """
    Compute binary indicator for overall Sustainability Stress tipping into the Extreme Band.
    """
    if ssi_band_col in df.columns:
        return (df[ssi_band_col].astype(str) == "Extreme").astype(int)
    elif "ssi_band" in df.columns:
        return (df["ssi_band"].astype(str) == "Extreme").astype(int)
    elif ssi_val_col in df.columns:
        return (df[ssi_val_col] >= threshold).astype(int)
    else:
        raise ValueError(f"No valid SSI band or score column found in DataFrame.")


def compute_all_events(
    df: pd.DataFrame,
    city_name: str | None = None,
    mode: Literal["statutory", "relative_tail", "hybrid"] = "hybrid",
) -> pd.DataFrame:
    """
    Enrich a panel DataFrame with all 4 standardized event flags.
    """
    out = df.copy()
    out["event_heatwave"] = compute_event_heatwave(out, mode=mode)
    out["event_smog"] = compute_event_smog(out, mode=mode)
    out["event_compound"] = compute_event_compound(out)
    out["event_extreme_ssi"] = compute_event_extreme_ssi(out)

    # Any statutory emergency event
    out["event_any_emergency"] = (
        (out["event_heatwave"] == 1)
        | (out["event_smog"] == 1)
        | (out["event_compound"] == 1)
        | (out["event_extreme_ssi"] == 1)
    ).astype(int)

    if city_name:
        out["city_id"] = city_name

    return out


def process_and_save_city_events(
    city: str,
    final_dir: str | Path = "data/h3_panel/final",
    v2_dir: str | Path = "data/h3_panel/v2",
    out_dir: str | Path = "data/h3_panel/ml_events",
    mode: Literal["statutory", "relative_tail", "hybrid"] = "hybrid",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Load raw and v2 panels for a city, join them, generate event flags,
    and save the combined panel to Parquet.
    """
    final_path = Path(final_dir) / f"{city}.parquet"
    v2_path = Path(v2_dir) / f"{city}.parquet"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not final_path.exists() or not v2_path.exists():
        raise FileNotFoundError(f"Missing input parquet for {city}: {final_path} or {v2_path}")

    df_final = pd.read_parquet(final_path)
    df_v2 = pd.read_parquet(v2_path)

    # Columns from final to merge: physical drivers + urban morphology + raw coordinates
    keep_final_cols = [
        c for c in df_final.columns
        if c not in df_v2.columns or c in ["h3_index", "date"]
    ]
    merged = pd.merge(df_final[keep_final_cols], df_v2, on=["h3_index", "date"], how="inner")

    # Compute events
    enriched = compute_all_events(merged, city_name=city, mode=mode)

    # Save enriched parquet
    out_path = out_dir / f"{city}.parquet"
    enriched.to_parquet(out_path, index=False)
    log.info(f"Saved {city} events panel ({len(enriched)} rows) -> {out_path}")

    # Summary metrics
    n_total = len(enriched)
    summary = {
        "city": city,
        "mode": mode,
        "total_hex_months": n_total,
        "unique_hexes": int(enriched["h3_index"].nunique()),
        "unique_dates": int(enriched["date"].nunique()),
        "event_prevalence": {
            "heatwave_share": round(float(enriched["event_heatwave"].mean()), 4),
            "heatwave_count": int(enriched["event_heatwave"].sum()),
            "smog_share": round(float(enriched["event_smog"].mean()), 4),
            "smog_count": int(enriched["event_smog"].sum()),
            "compound_share": round(float(enriched["event_compound"].mean()), 4),
            "compound_count": int(enriched["event_compound"].sum()),
            "extreme_ssi_share": round(float(enriched["event_extreme_ssi"].mean()), 4),
            "extreme_ssi_count": int(enriched["event_extreme_ssi"].sum()),
            "any_emergency_share": round(float(enriched["event_any_emergency"].mean()), 4),
            "any_emergency_count": int(enriched["event_any_emergency"].sum()),
        },
    }

    return enriched, summary


def run_event_labeling_pipeline(
    cities: list[str] | None = None,
    final_dir: str | Path = "data/h3_panel/final",
    v2_dir: str | Path = "data/h3_panel/v2",
    out_dir: str | Path = "data/h3_panel/ml_events",
    report_path: str | Path = "reports/ml_event_prevalence_summary.json",
    mode: Literal["statutory", "relative_tail", "hybrid"] = "hybrid",
) -> dict[str, Any]:
    """
    Run the complete Step 01 event labeling pipeline across all study cities.
    """
    if cities is None:
        cities = ["delhi", "mumbai", "kolkata", "hyderabad", "bikaner", "coimbatore", "indore"]

    all_summaries: dict[str, Any] = {}
    for c in cities:
        log.info(f"Processing event labels for {c} in mode '{mode}'...")
        _, summary = process_and_save_city_events(
            city=c, final_dir=final_dir, v2_dir=v2_dir, out_dir=out_dir, mode=mode
        )
        all_summaries[c] = summary

    # Save unified summary report in reports/
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as fh:
        json.dump(all_summaries, fh, indent=2)

    # Maintain provenance-tracked results in results/
    try:
        from src.utils.results_io import save_result
        save_result("ml_event_prevalence", all_summaries, config={"step": "01_event_definitions", "mode": mode, "seed": 20260101})
        log.info("Saved provenance-tracked result -> results/ml_event_prevalence.json")
    except Exception as exc:
        log.warning(f"Failed to save to results/: {exc}")

    log.info(f"Prevalence summary saved to {report_path}")
    return all_summaries


if __name__ == "__main__":
    summaries = run_event_labeling_pipeline()
    print("=== Step 01 Event Pre-Registration Summary ===")
    for city, stats in summaries.items():
        prev = stats["event_prevalence"]
        print(
            f"{city:12s} | Hexes: {stats['unique_hexes']:4d} | "
            f"Heatwave: {prev['heatwave_share']*100:5.1f}% | "
            f"Smog: {prev['smog_share']*100:5.1f}% | "
            f"Compound: {prev['compound_share']*100:5.1f}% | "
            f"Any Emer: {prev['any_emergency_share']*100:5.1f}%"
        )
