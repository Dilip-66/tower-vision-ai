from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# TowerVision AI
# Phase 1 - Quality Rule Optimization
# ============================================================
#
# Purpose:
#   Search for transparent multi-signal quality rules using the
#   controlled synthetic calibration benchmark.
#
# IMPORTANT:
#   This script DOES NOT modify images.
#   This script DOES NOT install production thresholds.
#
# It evaluates:
#
#   1. Blur
#      - sharpness
#      - gradient texture
#
#   2. Underexposure
#      - mean brightness
#      - dark pixel percentage
#
#   3. Overexposure
#      - mean brightness
#      - bright pixel percentage
#
# The optimization attempts to keep the false rejection rate
# on clean images <= CLEAN_FALSE_REJECTION_LIMIT while
# maximizing detection of synthetic degradation.
#
# Inputs:
#   data/reports/quality_calibration.csv
#   data/reports/quality_analysis.csv
#
# Outputs:
#   data/reports/quality_rule_optimization.csv
#   data/reports/quality_rule_candidates.json
#   data/reports/quality_rule_real_dataset_impact.csv
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_DIR = PROJECT_ROOT / "data" / "reports"

CALIBRATION_PATH = (
    REPORT_DIR / "quality_calibration.csv"
)

REAL_QUALITY_PATH = (
    REPORT_DIR / "quality_analysis.csv"
)

OPTIMIZATION_PATH = (
    REPORT_DIR / "quality_rule_optimization.csv"
)

CANDIDATE_PATH = (
    REPORT_DIR / "quality_rule_candidates.json"
)

REAL_IMPACT_PATH = (
    REPORT_DIR
    / "quality_rule_real_dataset_impact.csv"
)


CLEAN_FALSE_REJECTION_LIMIT = 0.05

# Threshold samples per metric (1,240-row benchmark — inexpensive).
THRESHOLD_POINTS = 25


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load synthetic calibration data and the original dataset
    quality measurements.
    """
    if not CALIBRATION_PATH.exists():
        raise FileNotFoundError(
            "quality_calibration.csv was not found.\n"
            "Run calibrate_quality.py first."
        )

    if not REAL_QUALITY_PATH.exists():
        raise FileNotFoundError(
            "quality_analysis.csv was not found.\n"
            "Run analyze_quality.py first."
        )

    calibration = pd.read_csv(
        CALIBRATION_PATH
    )

    real_quality = pd.read_csv(
        REAL_QUALITY_PATH
    )

    return calibration, real_quality


def clean_values(
    dataframe: pd.DataFrame,
    metric: str,
) -> np.ndarray:
    """
    Return finite clean-image values for a metric.
    """
    values = pd.to_numeric(
        dataframe.loc[
            dataframe["condition"] == "clean",
            metric,
        ],
        errors="coerce",
    )

    values = values.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    return values.to_numpy(
        dtype=float
    )


def bad_values(
    dataframe: pd.DataFrame,
    condition: str,
    metric: str,
) -> np.ndarray:
    """
    Return finite degraded-image values for a metric.
    """
    values = pd.to_numeric(
        dataframe.loc[
            dataframe["condition"] == condition,
            metric,
        ],
        errors="coerce",
    )

    values = values.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    return values.to_numpy(
        dtype=float
    )


def threshold_grid(
    values: np.ndarray,
) -> np.ndarray:
    """
    Generate threshold candidates based on observed data.
    """
    if len(values) == 0:
        return np.array([])

    low = float(
        np.min(values)
    )

    high = float(
        np.max(values)
    )

    if np.isclose(
        low,
        high,
    ):
        return np.array(
            [low]
        )

    return np.linspace(
        low,
        high,
        THRESHOLD_POINTS,
    )


def evaluate_lower_rule(
    clean: np.ndarray,
    bad: np.ndarray,
    threshold: float,
) -> tuple[float, float]:
    """
    Evaluate:

        value < threshold => degraded
    """
    clean_rejected = (
        clean < threshold
    )

    bad_detected = (
        bad < threshold
    )

    false_rejection = float(
        np.mean(
            clean_rejected
        )
    )

    detection_rate = float(
        np.mean(
            bad_detected
        )
    )

    return (
        false_rejection,
        detection_rate,
    )


def evaluate_higher_rule(
    clean: np.ndarray,
    bad: np.ndarray,
    threshold: float,
) -> tuple[float, float]:
    """
    Evaluate:

        value > threshold => degraded
    """
    clean_rejected = (
        clean > threshold
    )

    bad_detected = (
        bad > threshold
    )

    false_rejection = float(
        np.mean(
            clean_rejected
        )
    )

    detection_rate = float(
        np.mean(
            bad_detected
        )
    )

    return (
        false_rejection,
        detection_rate,
    )


def percentile_thresholds(
    dataframe: pd.DataFrame,
    metric: str,
) -> np.ndarray:
    """
    Generate thresholds using the observed calibration
    distribution.
    """
    values = pd.to_numeric(
        dataframe[metric],
        errors="coerce",
    )

    values = values.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    if values.empty:
        return np.array([])

    percentiles = np.linspace(
        1,
        99,
        THRESHOLD_POINTS,
    )

    return np.unique(
        np.percentile(
            values.to_numpy(
                dtype=float
            ),
            percentiles,
        )
    )


def evaluate_blur_rules(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Evaluate blur rules using:

        A) sharpness only
        B) gradient texture only
        C) sharpness AND gradient texture

    The AND rule is intentionally conservative:
    both indicators must suggest degradation.
    """
    clean_sharpness = clean_values(
        dataframe,
        "sharpness_laplacian",
    )

    clean_texture = clean_values(
        dataframe,
        "gradient_texture_mean",
    )

    bad_sharpness = bad_values(
        dataframe,
        "blur",
        "sharpness_laplacian",
    )

    bad_texture = bad_values(
        dataframe,
        "blur",
        "gradient_texture_mean",
    )

    sharpness_thresholds = (
        percentile_thresholds(
            dataframe,
            "sharpness_laplacian",
        )
    )

    texture_thresholds = (
        percentile_thresholds(
            dataframe,
            "gradient_texture_mean",
        )
    )

    results: list[dict[str, Any]] = []

    for threshold in (
        sharpness_thresholds
    ):
        clean_flags = (
            clean_sharpness
            < threshold
        )

        bad_flags = (
            bad_sharpness
            < threshold
        )

        false_rejection = float(
            np.mean(clean_flags)
        )

        detection_rate = float(
            np.mean(bad_flags)
        )

        results.append(
            {
                "problem": "blur",
                "rule": "sharpness_only",
                "threshold_1_name": (
                    "sharpness_laplacian"
                ),
                "threshold_1": float(
                    threshold
                ),
                "threshold_2_name": None,
                "threshold_2": None,
                "operator": None,
                "clean_false_rejection_rate": (
                    false_rejection
                ),
                "bad_detection_rate": (
                    detection_rate
                ),
                "score": (
                    detection_rate
                    - false_rejection
                ),
            }
        )

    for threshold in (
        texture_thresholds
    ):
        clean_flags = (
            clean_texture
            < threshold
        )

        bad_flags = (
            bad_texture
            < threshold
        )

        false_rejection = float(
            np.mean(clean_flags)
        )

        detection_rate = float(
            np.mean(bad_flags)
        )

        results.append(
            {
                "problem": "blur",
                "rule": "texture_only",
                "threshold_1_name": (
                    "gradient_texture_mean"
                ),
                "threshold_1": float(
                    threshold
                ),
                "threshold_2_name": None,
                "threshold_2": None,
                "operator": None,
                "clean_false_rejection_rate": (
                    false_rejection
                ),
                "bad_detection_rate": (
                    detection_rate
                ),
                "score": (
                    detection_rate
                    - false_rejection
                ),
            }
        )

    # Combined AND rule: both sharpness and texture must flag degradation.
    for sharpness_threshold in (
        sharpness_thresholds
    ):
        for texture_threshold in (
            texture_thresholds
        ):
            clean_flags = (
                (
                    clean_sharpness
                    < sharpness_threshold
                )
                &
                (
                    clean_texture
                    < texture_threshold
                )
            )

            bad_flags = (
                (
                    bad_sharpness
                    < sharpness_threshold
                )
                &
                (
                    bad_texture
                    < texture_threshold
                )
            )

            false_rejection = float(
                np.mean(clean_flags)
            )

            detection_rate = float(
                np.mean(bad_flags)
            )

            results.append(
                {
                    "problem": "blur",
                    "rule": (
                        "sharpness_and_texture"
                    ),
                    "threshold_1_name": (
                        "sharpness_laplacian"
                    ),
                    "threshold_1": float(
                        sharpness_threshold
                    ),
                    "threshold_2_name": (
                        "gradient_texture_mean"
                    ),
                    "threshold_2": float(
                        texture_threshold
                    ),
                    "operator": "AND",
                    "clean_false_rejection_rate": (
                        false_rejection
                    ),
                    "bad_detection_rate": (
                        detection_rate
                    ),
                    "score": (
                        detection_rate
                        - false_rejection
                    ),
                }
            )

    return results


def evaluate_underexposure_rules(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Evaluate underexposure using:

        mean brightness
        dark pixel percentage
        AND / OR combinations
    """
    clean_mean = clean_values(
        dataframe,
        "mean_brightness",
    )

    clean_dark = clean_values(
        dataframe,
        "dark_pixel_percentage",
    )

    bad_mean = bad_values(
        dataframe,
        "underexposed",
        "mean_brightness",
    )

    bad_dark = bad_values(
        dataframe,
        "underexposed",
        "dark_pixel_percentage",
    )

    mean_thresholds = percentile_thresholds(
        dataframe,
        "mean_brightness",
    )

    dark_thresholds = percentile_thresholds(
        dataframe,
        "dark_pixel_percentage",
    )

    results: list[dict[str, Any]] = []

    # Mean brightness alone.
    for threshold in mean_thresholds:
        clean_flags = (
            clean_mean < threshold
        )

        bad_flags = (
            bad_mean < threshold
        )

        false_rejection = float(
            np.mean(clean_flags)
        )

        detection_rate = float(
            np.mean(bad_flags)
        )

        results.append(
            {
                "problem": "underexposure",
                "rule": "mean_brightness_only",
                "threshold_1_name": (
                    "mean_brightness"
                ),
                "threshold_1": float(
                    threshold
                ),
                "threshold_2_name": None,
                "threshold_2": None,
                "operator": None,
                "clean_false_rejection_rate": (
                    false_rejection
                ),
                "bad_detection_rate": (
                    detection_rate
                ),
                "score": (
                    detection_rate
                    - false_rejection
                ),
            }
        )

    # Dark pixels alone.
    for threshold in dark_thresholds:
        clean_flags = (
            clean_dark > threshold
        )

        bad_flags = (
            bad_dark > threshold
        )

        false_rejection = float(
            np.mean(clean_flags)
        )

        detection_rate = float(
            np.mean(bad_flags)
        )

        results.append(
            {
                "problem": "underexposure",
                "rule": "dark_pixels_only",
                "threshold_1_name": (
                    "dark_pixel_percentage"
                ),
                "threshold_1": float(
                    threshold
                ),
                "threshold_2_name": None,
                "threshold_2": None,
                "operator": None,
                "clean_false_rejection_rate": (
                    false_rejection
                ),
                "bad_detection_rate": (
                    detection_rate
                ),
                "score": (
                    detection_rate
                    - false_rejection
                ),
            }
        )

    for mean_threshold in mean_thresholds:
        for dark_threshold in (
            dark_thresholds
        ):
            mean_clean = (
                clean_mean
                < mean_threshold
            )

            dark_clean = (
                clean_dark
                > dark_threshold
            )

            mean_bad = (
                bad_mean
                < mean_threshold
            )

            dark_bad = (
                bad_dark
                > dark_threshold
            )

            # AND rule.
            clean_and = (
                mean_clean & dark_clean
            )

            bad_and = (
                mean_bad & dark_bad
            )

            false_rejection = float(
                np.mean(clean_and)
            )

            detection_rate = float(
                np.mean(bad_and)
            )

            results.append(
                {
                    "problem": "underexposure",
                    "rule": (
                        "mean_and_dark_pixels"
                    ),
                    "threshold_1_name": (
                        "mean_brightness"
                    ),
                    "threshold_1": float(
                        mean_threshold
                    ),
                    "threshold_2_name": (
                        "dark_pixel_percentage"
                    ),
                    "threshold_2": float(
                        dark_threshold
                    ),
                    "operator": "AND",
                    "clean_false_rejection_rate": (
                        false_rejection
                    ),
                    "bad_detection_rate": (
                        detection_rate
                    ),
                    "score": (
                        detection_rate
                        - false_rejection
                    ),
                }
            )

            # OR rule.
            clean_or = (
                mean_clean | dark_clean
            )

            bad_or = (
                mean_bad | dark_bad
            )

            false_rejection = float(
                np.mean(clean_or)
            )

            detection_rate = float(
                np.mean(bad_or)
            )

            results.append(
                {
                    "problem": "underexposure",
                    "rule": (
                        "mean_or_dark_pixels"
                    ),
                    "threshold_1_name": (
                        "mean_brightness"
                    ),
                    "threshold_1": float(
                        mean_threshold
                    ),
                    "threshold_2_name": (
                        "dark_pixel_percentage"
                    ),
                    "threshold_2": float(
                        dark_threshold
                    ),
                    "operator": "OR",
                    "clean_false_rejection_rate": (
                        false_rejection
                    ),
                    "bad_detection_rate": (
                        detection_rate
                    ),
                    "score": (
                        detection_rate
                        - false_rejection
                    ),
                }
            )

    return results


def evaluate_overexposure_rules(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Evaluate overexposure using:

        mean brightness
        bright pixel percentage
        AND / OR combinations
    """
    clean_mean = clean_values(
        dataframe,
        "mean_brightness",
    )

    clean_bright = clean_values(
        dataframe,
        "bright_pixel_percentage",
    )

    bad_mean = bad_values(
        dataframe,
        "overexposed",
        "mean_brightness",
    )

    bad_bright = bad_values(
        dataframe,
        "overexposed",
        "bright_pixel_percentage",
    )

    mean_thresholds = percentile_thresholds(
        dataframe,
        "mean_brightness",
    )

    bright_thresholds = (
        percentile_thresholds(
            dataframe,
            "bright_pixel_percentage",
        )
    )

    results: list[dict[str, Any]] = []

    for threshold in mean_thresholds:
        clean_flags = (
            clean_mean > threshold
        )

        bad_flags = (
            bad_mean > threshold
        )

        false_rejection = float(
            np.mean(clean_flags)
        )

        detection_rate = float(
            np.mean(bad_flags)
        )

        results.append(
            {
                "problem": "overexposure",
                "rule": "mean_brightness_only",
                "threshold_1_name": (
                    "mean_brightness"
                ),
                "threshold_1": float(
                    threshold
                ),
                "threshold_2_name": None,
                "threshold_2": None,
                "operator": None,
                "clean_false_rejection_rate": (
                    false_rejection
                ),
                "bad_detection_rate": (
                    detection_rate
                ),
                "score": (
                    detection_rate
                    - false_rejection
                ),
            }
        )

    for threshold in bright_thresholds:
        clean_flags = (
            clean_bright > threshold
        )

        bad_flags = (
            bad_bright > threshold
        )

        false_rejection = float(
            np.mean(clean_flags)
        )

        detection_rate = float(
            np.mean(bad_flags)
        )

        results.append(
            {
                "problem": "overexposure",
                "rule": (
                    "bright_pixels_only"
                ),
                "threshold_1_name": (
                    "bright_pixel_percentage"
                ),
                "threshold_1": float(
                    threshold
                ),
                "threshold_2_name": None,
                "threshold_2": None,
                "operator": None,
                "clean_false_rejection_rate": (
                    false_rejection
                ),
                "bad_detection_rate": (
                    detection_rate
                ),
                "score": (
                    detection_rate
                    - false_rejection
                ),
            }
        )

    for mean_threshold in mean_thresholds:
        for bright_threshold in (
            bright_thresholds
        ):
            mean_clean = (
                clean_mean
                > mean_threshold
            )

            bright_clean = (
                clean_bright
                > bright_threshold
            )

            mean_bad = (
                bad_mean
                > mean_threshold
            )

            bright_bad = (
                bad_bright
                > bright_threshold
            )

            # AND:
            # both metrics must indicate overexposure.
            clean_and = (
                mean_clean & bright_clean
            )

            bad_and = (
                mean_bad & bright_bad
            )

            false_rejection = float(
                np.mean(clean_and)
            )

            detection_rate = float(
                np.mean(bad_and)
            )

            results.append(
                {
                    "problem": "overexposure",
                    "rule": (
                        "mean_and_bright_pixels"
                    ),
                    "threshold_1_name": (
                        "mean_brightness"
                    ),
                    "threshold_1": float(
                        mean_threshold
                    ),
                    "threshold_2_name": (
                        "bright_pixel_percentage"
                    ),
                    "threshold_2": float(
                        bright_threshold
                    ),
                    "operator": "AND",
                    "clean_false_rejection_rate": (
                        false_rejection
                    ),
                    "bad_detection_rate": (
                        detection_rate
                    ),
                    "score": (
                        detection_rate
                        - false_rejection
                    ),
                }
            )

            # OR:
            # either metric is enough to indicate overexposure.
            clean_or = (
                mean_clean | bright_clean
            )

            bad_or = (
                mean_bad | bright_bad
            )

            false_rejection = float(
                np.mean(clean_or)
            )

            detection_rate = float(
                np.mean(bad_or)
            )

            results.append(
                {
                    "problem": "overexposure",
                    "rule": (
                        "mean_or_bright_pixels"
                    ),
                    "threshold_1_name": (
                        "mean_brightness"
                    ),
                    "threshold_1": float(
                        mean_threshold
                    ),
                    "threshold_2_name": (
                        "bright_pixel_percentage"
                    ),
                    "threshold_2": float(
                        bright_threshold
                    ),
                    "operator": "OR",
                    "clean_false_rejection_rate": (
                        false_rejection
                    ),
                    "bad_detection_rate": (
                        detection_rate
                    ),
                    "score": (
                        detection_rate
                        - false_rejection
                    ),
                }
            )

    return results


def select_best_candidates(
    optimization_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select the best valid candidate for each problem.

    Constraint:
        clean false rejection <= 5%

    Objective:
        maximize degradation detection rate.

    Tie breaker:
        maximize the separation score.
    """
    valid = optimization_dataframe[
        optimization_dataframe[
            "clean_false_rejection_rate"
        ]
        <= CLEAN_FALSE_REJECTION_LIMIT
    ].copy()

    if valid.empty:
        return pd.DataFrame()

    valid = valid.sort_values(
        [
            "problem",
            "bad_detection_rate",
            "score",
        ],
        ascending=[
            True,
            False,
            False,
        ],
    )

    return (
        valid
        .groupby(
            "problem",
            as_index=False,
        )
        .head(1)
        .reset_index(drop=True)
    )


def apply_candidate_to_real_data(
    real_quality: pd.DataFrame,
    candidate: dict[str, Any],
) -> pd.Series:
    """
    Apply one optimized candidate to the real dataset.
    """
    metric_1 = candidate[
        "threshold_1_name"
    ]

    threshold_1 = candidate[
        "threshold_1"
    ]

    metric_2 = candidate[
        "threshold_2_name"
    ]

    threshold_2 = candidate[
        "threshold_2"
    ]

    problem = candidate[
        "problem"
    ]

    if (
        pd.isna(metric_1)
        or pd.isna(threshold_1)
    ):
        return pd.Series(
            False,
            index=real_quality.index,
        )

    values_1 = pd.to_numeric(
        real_quality[metric_1],
        errors="coerce",
    )

    if problem == "blur":
        condition_1 = (
            values_1 < threshold_1
        )
    else:
        condition_1 = (
            values_1 > threshold_1
        )

    if (
        pd.isna(metric_2)
        or pd.isna(threshold_2)
        or pd.isna(candidate["operator"])
    ):
        return condition_1.fillna(
            False
        )

    values_2 = pd.to_numeric(
        real_quality[metric_2],
        errors="coerce",
    )

    if problem == "blur":
        condition_2 = (
            values_2 < threshold_2
        )
    else:
        condition_2 = (
            values_2 > threshold_2
        )

    if candidate["operator"] == "AND":
        result = (
            condition_1
            & condition_2
        )
    else:
        result = (
            condition_1
            | condition_2
        )

    return result.fillna(
        False
    )


def build_real_dataset_impact(
    real_quality: pd.DataFrame,
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    """
    Measure how many actual dataset frames would be flagged by
    each candidate.
    """
    records: list[dict[str, Any]] = []

    for _, candidate_row in (
        candidates.iterrows()
    ):
        candidate = candidate_row.to_dict()

        flags = apply_candidate_to_real_data(
            real_quality,
            candidate,
        )

        flagged = (
            real_quality[flags]
        )

        records.append(
            {
                "problem": candidate[
                    "problem"
                ],
                "rule": candidate[
                    "rule"
                ],
                "threshold_1_name": candidate[
                    "threshold_1_name"
                ],
                "threshold_1": candidate[
                    "threshold_1"
                ],
                "threshold_2_name": candidate[
                    "threshold_2_name"
                ],
                "threshold_2": candidate[
                    "threshold_2"
                ],
                "operator": candidate[
                    "operator"
                ],
                "real_frames_analyzed": len(
                    real_quality
                ),
                "real_frames_flagged": int(
                    flags.sum()
                ),
                "real_flag_rate": float(
                    flags.mean()
                ),
                "flagged_frame_ids": json.dumps(
                    flagged[
                        "frame_id"
                    ]
                    .astype(str)
                    .tolist()
                ),
            }
        )

    return pd.DataFrame(
        records
    )


def save_outputs(
    optimization: pd.DataFrame,
    candidates: pd.DataFrame,
    real_impact: pd.DataFrame,
) -> None:
    """
    Save all optimization outputs.
    """
    optimization.to_csv(
        OPTIMIZATION_PATH,
        index=False,
        encoding="utf-8",
    )

    real_impact.to_csv(
        REAL_IMPACT_PATH,
        index=False,
        encoding="utf-8",
    )

    # Sanitize NaN / NA to None for valid JSON (None -> null)
    candidates_for_json = candidates.replace({np.nan: None})
    candidates_for_json = candidates_for_json.where(
        pd.notna(candidates_for_json), None
    )

    payload = {
        "false_rejection_constraint": (
            CLEAN_FALSE_REJECTION_LIMIT
        ),
        "candidates": (
            candidates_for_json.to_dict(
                orient="records"
            )
        ),
        "important_note": (
            "Candidates are not production rules. "
            "They require visual review before deployment."
        ),
    }

    with CANDIDATE_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
        )

    print()
    print(
        f"Optimization CSV : {OPTIMIZATION_PATH}"
    )

    print(
        f"Candidate JSON   : {CANDIDATE_PATH}"
    )

    print(
        f"Real impact CSV  : {REAL_IMPACT_PATH}"
    )


def print_candidates(
    candidates: pd.DataFrame,
    real_impact: pd.DataFrame,
) -> None:
    """
    Print the selected candidates and their effect on the real
    dataset.
    """
    print()
    print("=" * 72)
    print(
        "QUALITY RULE OPTIMIZATION RESULTS"
    )
    print("=" * 72)

    print()
    print(
        f"Maximum clean false rejection: "
        f"{CLEAN_FALSE_REJECTION_LIMIT * 100:.1f}%"
    )

    if candidates.empty:
        print()
        print(
            "No candidate satisfied the clean-image constraint."
        )
        return

    for _, row in candidates.iterrows():
        print()
        print(
            f"PROBLEM: {row['problem']}"
        )
        print("-" * 72)

        print(
            f"Rule                    : "
            f"{row['rule']}"
        )

        print(
            f"{row['threshold_1_name']} : "
            f"{row['threshold_1']}"
        )

        if not pd.isna(
            row["threshold_2_name"]
        ):
            print(
                f"{row['threshold_2_name']} : "
                f"{row['threshold_2']}"
            )

            print(
                f"Operator                : "
                f"{row['operator']}"
            )

        print(
            f"Clean false rejection   : "
            f"{row['clean_false_rejection_rate'] * 100:.2f}%"
        )

        print(
            f"Synthetic detection     : "
            f"{row['bad_detection_rate'] * 100:.2f}%"
        )

        print(
            f"Separation score        : "
            f"{row['score']:.4f}"
        )

        impact_rows = real_impact[
            real_impact["problem"]
            == row["problem"]
        ]

        impact_rows = impact_rows[
            impact_rows["rule"]
            == row["rule"]
        ]

        if not impact_rows.empty:
            impact = impact_rows.iloc[0]

            print(
                f"Real frames flagged    : "
                f"{impact['real_frames_flagged']} / "
                f"{impact['real_frames_analyzed']}"
            )

            print(
                f"Real dataset flag rate  : "
                f"{impact['real_flag_rate'] * 100:.2f}%"
            )

    print()
    print("=" * 72)
    print(
        "IMPORTANT: VISUAL REVIEW IS STILL REQUIRED"
    )
    print("=" * 72)
    print()


def main() -> None:
    """
    Main entry point.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - QUALITY RULE OPTIMIZATION"
    )
    print("=" * 72)
    print()

    calibration, real_quality = (
        load_data()
    )

    print(
        f"Calibration rows : "
        f"{len(calibration)}"
    )

    print(
        f"Real quality rows: "
        f"{len(real_quality)}"
    )

    print()
    print(
        "Evaluating blur rules..."
    )

    blur_results = evaluate_blur_rules(
        calibration
    )

    print(
        "Evaluating underexposure rules..."
    )

    underexposure_results = (
        evaluate_underexposure_rules(
            calibration
        )
    )

    print(
        "Evaluating overexposure rules..."
    )

    overexposure_results = (
        evaluate_overexposure_rules(
            calibration
        )
    )

    all_results = (
        blur_results
        + underexposure_results
        + overexposure_results
    )

    optimization_dataframe = pd.DataFrame(
        all_results
    )

    candidates = select_best_candidates(
        optimization_dataframe
    )

    real_impact = (
        build_real_dataset_impact(
            real_quality=real_quality,
            candidates=candidates,
        )
    )

    save_outputs(
        optimization=optimization_dataframe,
        candidates=candidates,
        real_impact=real_impact,
    )

    print_candidates(
        candidates=candidates,
        real_impact=real_impact,
    )


if __name__ == "__main__":
    main()