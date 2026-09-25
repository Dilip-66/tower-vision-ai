from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
from PIL import Image


# ============================================================
# TowerVision AI
# Phase 1 - Quality Gate Calibration
# ============================================================
#
# Purpose:
#   Build a controlled benchmark for calibrating the image
#   quality gate.
#
# We create synthetic versions of representative organizer
# images:
#
#   CLEAN
#   BLUR
#   UNDEREXPOSED
#   OVEREXPOSED
#
# Important:
#   The original organizer data is NEVER modified.
#
# Output:
#
#   data/reports/quality_calibration.csv
#   data/reports/quality_calibration.json
#
#   data/interim/quality_benchmark/
#       clean/
#       blur/
#       underexposed/
#       overexposed/
#
# The synthetic images are calibration data only. They are not
# counted as additional organizer-provided images.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"

CATALOG_PATH = REPORT_DIR / "image_catalog.csv"

SUPPORTED_FORMATS = {
    "JPEG",
    "MPO",
    "PNG",
    "WEBP",
    "BMP",
    "TIFF",
}

ANALYSIS_WIDTH = 1024
ANALYSIS_HEIGHT = 1024

# Deterministic seed so the benchmark is reproducible.
RANDOM_SEED = 42

# Maximum number of original source groups used for calibration.
# 124 is small enough for the full dataset.
MAX_SOURCE_GROUPS = 124

# Blur sigma values.
BLUR_LEVELS = {
    "mild": 1.5,
    "moderate": 3.0,
    "severe": 6.0,
}

# Gamma < 1 brightens an image.
# Gamma > 1 darkens an image.
UNDEREXPOSURE_LEVELS = {
    "mild": 1.5,
    "moderate": 2.0,
    "severe": 3.0,
}

OVEREXPOSURE_LEVELS = {
    "mild": 0.70,
    "moderate": 0.45,
    "severe": 0.25,
}


def load_catalog() -> pd.DataFrame:
    """
    Load the master image catalog.
    """
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            "image_catalog.csv was not found.\n"
            "Run build_image_catalog.py first."
        )

    dataframe = pd.read_csv(
        CATALOG_PATH
    )

    required_columns = {
        "frame_id",
        "source_group_id",
        "source_relative_path",
        "frame_index",
        "status",
        "source_format",
    }

    missing = (
        required_columns
        - set(dataframe.columns)
    )

    if missing:
        raise ValueError(
            "image_catalog.csv is missing "
            f"required columns: {sorted(missing)}"
        )

    return dataframe


def select_representative_frames(
    catalog: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select exactly one representative frame per source group.

    For MPO sources this means frame 0 is used.

    We deliberately do NOT use both MPO frames here because
    calibration samples should represent independent source
    groups rather than duplicate correlated views.
    """
    valid = catalog[
        catalog["status"] == "valid"
    ].copy()

    valid = valid.sort_values(
        [
            "source_group_id",
            "frame_index",
        ]
    )

    representatives = (
        valid
        .groupby(
            "source_group_id",
            as_index=False,
        )
        .first()
    )

    representatives = representatives.head(
        MAX_SOURCE_GROUPS
    )

    return representatives


def decode_frame(
    relative_path: str,
    frame_index: int,
) -> np.ndarray:
    """
    Decode one image/frame as grayscale.
    """
    path = (
        PROJECT_ROOT
        / relative_path
    )

    with Image.open(path) as image:
        image.seek(frame_index)

        frame = image.convert(
            "L"
        ).copy()

    return np.asarray(
        frame,
        dtype=np.uint8,
    )


def resize_for_analysis(
    grayscale: np.ndarray,
) -> np.ndarray:
    """
    Resize while maintaining the original aspect ratio.
    """
    height, width = grayscale.shape[:2]

    if width <= 0 or height <= 0:
        raise ValueError(
            "Invalid image dimensions."
        )

    scale = min(
        ANALYSIS_WIDTH / width,
        ANALYSIS_HEIGHT / height,
        1.0,
    )

    if scale == 1.0:
        return grayscale.copy()

    new_width = max(
        1,
        int(round(width * scale)),
    )

    new_height = max(
        1,
        int(round(height * scale)),
    )

    return cv2.resize(
        grayscale,
        (
            new_width,
            new_height,
        ),
        interpolation=cv2.INTER_AREA,
    )


def calculate_sharpness(
    grayscale: np.ndarray,
) -> float:
    """
    Variance of the Laplacian.
    """
    laplacian = cv2.Laplacian(
        grayscale,
        cv2.CV_64F,
    )

    return float(
        np.var(laplacian)
    )


def calculate_brightness_metrics(
    grayscale: np.ndarray,
) -> dict[str, float]:
    """
    Calculate brightness, clipping and dynamic-range metrics.
    """
    pixels = grayscale.astype(
        np.float32
    )

    percentiles = np.percentile(
        pixels,
        [
            1,
            5,
            25,
            50,
            75,
            95,
            99,
        ],
    )

    return {
        "mean_brightness": float(
            np.mean(pixels)
        ),
        "brightness_std": float(
            np.std(pixels)
        ),
        "p01_brightness": float(
            percentiles[0]
        ),
        "p05_brightness": float(
            percentiles[1]
        ),
        "p25_brightness": float(
            percentiles[2]
        ),
        "p50_brightness": float(
            percentiles[3]
        ),
        "p75_brightness": float(
            percentiles[4]
        ),
        "p95_brightness": float(
            percentiles[5]
        ),
        "p99_brightness": float(
            percentiles[6]
        ),
        "dark_pixel_percentage": float(
            np.mean(
                pixels <= 32
            )
            * 100.0
        ),
        "bright_pixel_percentage": float(
            np.mean(
                pixels >= 223
            )
            * 100.0
        ),
        "dynamic_range": float(
            percentiles[5]
            - percentiles[1]
        ),
    }


def calculate_gradient_texture(
    grayscale: np.ndarray,
) -> float:
    """
    Calculate average gradient magnitude.
    """
    sobel_x = cv2.Sobel(
        grayscale,
        cv2.CV_32F,
        1,
        0,
        ksize=3,
    )

    sobel_y = cv2.Sobel(
        grayscale,
        cv2.CV_32F,
        0,
        1,
        ksize=3,
    )

    magnitude = cv2.magnitude(
        sobel_x,
        sobel_y,
    )

    return float(
        np.mean(magnitude)
    )


def calculate_metrics(
    image: np.ndarray,
) -> dict[str, float]:
    """
    Calculate all quality metrics for an image.
    """
    analyzed = resize_for_analysis(
        image
    )

    brightness = calculate_brightness_metrics(
        analyzed
    )

    return {
        "width": int(
            analyzed.shape[1]
        ),
        "height": int(
            analyzed.shape[0]
        ),
        "sharpness_laplacian": (
            calculate_sharpness(
                analyzed
            )
        ),
        "gradient_texture_mean": (
            calculate_gradient_texture(
                analyzed
            )
        ),
        **brightness,
    }


def apply_gaussian_blur(
    image: np.ndarray,
    sigma: float,
) -> np.ndarray:
    """
    Create a controlled blurred image.
    """
    kernel_size = int(
        max(
            3,
            round(
                sigma * 6
            ) | 1,
        )
    )

    return cv2.GaussianBlur(
        image,
        (
            kernel_size,
            kernel_size,
        ),
        sigmaX=sigma,
        sigmaY=sigma,
    )


def apply_gamma(
    image: np.ndarray,
    gamma: float,
) -> np.ndarray:
    """
    Apply gamma transformation.

    gamma > 1 -> darker
    gamma < 1 -> brighter
    """
    normalized = image.astype(
        np.float32
    ) / 255.0

    transformed = np.power(
        normalized,
        gamma,
    )

    return np.clip(
        transformed * 255.0,
        0,
        255,
    ).astype(
        np.uint8
    )


def create_benchmark_record(
    source_row: pd.Series,
    condition: str,
    severity: str,
    image: np.ndarray,
) -> dict[str, Any]:
    """
    Measure one benchmark image.
    """
    metrics = calculate_metrics(
        image
    )

    return {
        "source_group_id": source_row[
            "source_group_id"
        ],
        "source_file_name": source_row[
            "source_file_name"
        ],
        "source_frame_id": source_row[
            "frame_id"
        ],
        "source_format": source_row[
            "source_format"
        ],
        "condition": condition,
        "severity": severity,
        "synthetic": condition != "clean",
        **metrics,
    }


def save_image(
    image: np.ndarray,
    output_path: Path,
) -> None:
    """
    Save a benchmark image as JPEG.
    """
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    success = cv2.imwrite(
        str(output_path),
        image,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            90,
        ],
    )

    if not success:
        raise IOError(
            f"Failed to save image: {output_path}"
        )


def create_benchmark(
    representatives: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Create the complete controlled quality benchmark.
    """
    records: list[dict[str, Any]] = []

    total = len(representatives)

    for index, (_, source_row) in enumerate(
        representatives.iterrows(),
        start=1,
    ):
        print(
            f"[{index:03d}/{total:03d}] "
            f"{source_row['source_group_id']}"
        )

        source_image = decode_frame(
            relative_path=str(
                source_row[
                    "source_relative_path"
                ]
            ),
            frame_index=int(
                source_row[
                    "frame_index"
                ]
            ),
        )

        # ----------------------------------------------------
        # CLEAN
        # ----------------------------------------------------

        clean_output = (
            INTERIM_DIR
            / "quality_benchmark"
            / "clean"
            / (
                f"{source_row['source_group_id']}"
                "_clean.jpg"
            )
        )

        save_image(
            source_image,
            clean_output,
        )

        records.append(
            create_benchmark_record(
                source_row=source_row,
                condition="clean",
                severity="none",
                image=source_image,
            )
        )

        # ----------------------------------------------------
        # BLUR
        # ----------------------------------------------------

        for severity, sigma in (
            BLUR_LEVELS.items()
        ):
            blurred = apply_gaussian_blur(
                source_image,
                sigma,
            )

            output_path = (
                INTERIM_DIR
                / "quality_benchmark"
                / "blur"
                / severity
                / (
                    f"{source_row['source_group_id']}"
                    f"_blur_{severity}.jpg"
                )
            )

            save_image(
                blurred,
                output_path,
            )

            records.append(
                create_benchmark_record(
                    source_row=source_row,
                    condition="blur",
                    severity=severity,
                    image=blurred,
                )
            )

        # ----------------------------------------------------
        # UNDEREXPOSURE
        # ----------------------------------------------------

        for severity, gamma in (
            UNDEREXPOSURE_LEVELS.items()
        ):
            darkened = apply_gamma(
                source_image,
                gamma,
            )

            output_path = (
                INTERIM_DIR
                / "quality_benchmark"
                / "underexposed"
                / severity
                / (
                    f"{source_row['source_group_id']}"
                    f"_underexposed_{severity}.jpg"
                )
            )

            save_image(
                darkened,
                output_path,
            )

            records.append(
                create_benchmark_record(
                    source_row=source_row,
                    condition="underexposed",
                    severity=severity,
                    image=darkened,
                )
            )

        # ----------------------------------------------------
        # OVEREXPOSURE
        # ----------------------------------------------------

        for severity, gamma in (
            OVEREXPOSURE_LEVELS.items()
        ):
            brightened = apply_gamma(
                source_image,
                gamma,
            )

            output_path = (
                INTERIM_DIR
                / "quality_benchmark"
                / "overexposed"
                / severity
                / (
                    f"{source_row['source_group_id']}"
                    f"_overexposed_{severity}.jpg"
                )
            )

            save_image(
                brightened,
                output_path,
            )

            records.append(
                create_benchmark_record(
                    source_row=source_row,
                    condition="overexposed",
                    severity=severity,
                    image=brightened,
                )
            )

        source_image = None

    return records


def find_best_threshold_for_lower_is_bad(
    dataframe: pd.DataFrame,
    clean_condition: str,
    bad_condition: str,
    metric: str,
) -> dict[str, Any]:
    """
    Find a candidate threshold where:

        metric < threshold => reject

    This is used for blur and underexposure.

    The threshold is selected from observed benchmark values.

    IMPORTANT:
    This is a calibration candidate, not an unquestionable
    production threshold.
    """
    clean_values = dataframe[
        dataframe["condition"]
        == clean_condition
    ][metric].dropna().values

    bad_values = dataframe[
        dataframe["condition"]
        == bad_condition
    ][metric].dropna().values

    if len(clean_values) == 0 or len(bad_values) == 0:
        return {
            "metric": metric,
            "direction": "lower_is_bad",
            "threshold": None,
            "accuracy": None,
            "clean_false_rejection_rate": None,
            "bad_detection_rate": None,
        }

    candidates = np.unique(
        np.concatenate(
            [
                clean_values,
                bad_values,
            ]
        )
    )

    best: dict[str, Any] | None = None

    for threshold in candidates:
        clean_rejected = (
            clean_values < threshold
        )

        bad_detected = (
            bad_values < threshold
        )

        clean_false_rejection_rate = float(
            np.mean(
                clean_rejected
            )
        )

        bad_detection_rate = float(
            np.mean(
                bad_detected
            )
        )

        accuracy = (
            (
                np.sum(~clean_rejected)
                + np.sum(bad_detected)
            )
            / (
                len(clean_values)
                + len(bad_values)
            )
        )

        score = (
            bad_detection_rate
            - clean_false_rejection_rate
        )

        candidate = {
            "metric": metric,
            "direction": "lower_is_bad",
            "threshold": float(
                threshold
            ),
            "accuracy": float(
                accuracy
            ),
            "clean_false_rejection_rate": (
                clean_false_rejection_rate
            ),
            "bad_detection_rate": (
                bad_detection_rate
            ),
            "score": float(score),
        }

        if (
            best is None
            or candidate["score"]
            > best["score"]
        ):
            best = candidate

    return best


def find_best_threshold_for_higher_is_bad(
    dataframe: pd.DataFrame,
    clean_condition: str,
    bad_condition: str,
    metric: str,
) -> dict[str, Any]:
    """
    Find a candidate threshold where:

        metric > threshold => reject

    This is used for overexposure.
    """
    clean_values = dataframe[
        dataframe["condition"]
        == clean_condition
    ][metric].dropna().values

    bad_values = dataframe[
        dataframe["condition"]
        == bad_condition
    ][metric].dropna().values

    if len(clean_values) == 0 or len(bad_values) == 0:
        return {
            "metric": metric,
            "direction": "higher_is_bad",
            "threshold": None,
            "accuracy": None,
            "clean_false_rejection_rate": None,
            "bad_detection_rate": None,
        }

    candidates = np.unique(
        np.concatenate(
            [
                clean_values,
                bad_values,
            ]
        )
    )

    best: dict[str, Any] | None = None

    for threshold in candidates:
        clean_rejected = (
            clean_values > threshold
        )

        bad_detected = (
            bad_values > threshold
        )

        clean_false_rejection_rate = float(
            np.mean(
                clean_rejected
            )
        )

        bad_detection_rate = float(
            np.mean(
                bad_detected
            )
        )

        accuracy = (
            (
                np.sum(~clean_rejected)
                + np.sum(bad_detected)
            )
            / (
                len(clean_values)
                + len(bad_values)
            )
        )

        score = (
            bad_detection_rate
            - clean_false_rejection_rate
        )

        candidate = {
            "metric": metric,
            "direction": "higher_is_bad",
            "threshold": float(
                threshold
            ),
            "accuracy": float(
                accuracy
            ),
            "clean_false_rejection_rate": (
                clean_false_rejection_rate
            ),
            "bad_detection_rate": (
                bad_detection_rate
            ),
            "score": float(score),
        }

        if (
            best is None
            or candidate["score"]
            > best["score"]
        ):
            best = candidate

    return best


def build_calibration_candidates(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Evaluate simple candidate threshold rules.

    We keep blur, underexposure and overexposure separate.
    """
    return {
        "blur_sharpness": (
            find_best_threshold_for_lower_is_bad(
                dataframe=dataframe,
                clean_condition="clean",
                bad_condition="blur",
                metric="sharpness_laplacian",
            )
        ),
        "underexposure_mean_brightness": (
            find_best_threshold_for_lower_is_bad(
                dataframe=dataframe,
                clean_condition="clean",
                bad_condition="underexposed",
                metric="mean_brightness",
            )
        ),
        "underexposure_dark_pixels": (
            find_best_threshold_for_higher_is_bad(
                dataframe=dataframe,
                clean_condition="clean",
                bad_condition="underexposed",
                metric="dark_pixel_percentage",
            )
        ),
        "overexposure_mean_brightness": (
            find_best_threshold_for_higher_is_bad(
                dataframe=dataframe,
                clean_condition="clean",
                bad_condition="overexposed",
                metric="mean_brightness",
            )
        ),
        "overexposure_bright_pixels": (
            find_best_threshold_for_higher_is_bad(
                dataframe=dataframe,
                clean_condition="clean",
                bad_condition="overexposed",
                metric="bright_pixel_percentage",
            )
        ),
    }


def summarize_conditions(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Produce distributions grouped by condition and severity.
    """
    result: dict[str, Any] = {}

    metrics = [
        "sharpness_laplacian",
        "mean_brightness",
        "brightness_std",
        "dark_pixel_percentage",
        "bright_pixel_percentage",
        "dynamic_range",
        "gradient_texture_mean",
    ]

    for (
        condition,
        condition_dataframe,
    ) in dataframe.groupby(
        "condition"
    ):
        result[condition] = {}

        for metric in metrics:
            values = pd.to_numeric(
                condition_dataframe[metric],
                errors="coerce",
            ).dropna()

            if values.empty:
                continue

            result[condition][metric] = {
                "minimum": float(
                    values.min()
                ),
                "p05": float(
                    values.quantile(0.05)
                ),
                "median": float(
                    values.median()
                ),
                "p95": float(
                    values.quantile(0.95)
                ),
                "maximum": float(
                    values.max()
                ),
                "mean": float(
                    values.mean()
                ),
            }

    return result


def save_outputs(
    dataframe: pd.DataFrame,
    calibration_candidates: dict[str, Any],
    condition_summary: dict[str, Any],
) -> None:
    """
    Save CSV and JSON calibration reports.
    """
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        REPORT_DIR
        / "quality_calibration.csv"
    )

    json_path = (
        REPORT_DIR
        / "quality_calibration.json"
    )

    dataframe.to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    payload = {
        "benchmark": {
            "original_source_groups": int(
                dataframe[
                    "source_group_id"
                ].nunique()
            ),
            "rows": int(
                len(dataframe)
            ),
            "note": (
                "Synthetic corruptions are calibration "
                "examples and are not additional "
                "organizer-provided images."
            ),
        },
        "condition_summary": condition_summary,
        "candidate_thresholds": (
            calibration_candidates
        ),
    }

    with json_path.open(
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
        f"CSV report : {csv_path}"
    )

    print(
        f"JSON report: {json_path}"
    )


def print_summary(
    dataframe: pd.DataFrame,
    calibration_candidates: dict[str, Any],
) -> None:
    """
    Print the important calibration information.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - QUALITY GATE CALIBRATION"
    )
    print("=" * 72)

    print()
    print(
        "BENCHMARK SIZE"
    )
    print("-" * 72)

    print(
        "Original source groups : "
        f"{dataframe['source_group_id'].nunique()}"
    )

    print(
        "Benchmark rows         : "
        f"{len(dataframe)}"
    )

    print()
    print(
        "CONDITION COUNTS"
    )
    print("-" * 72)

    condition_counts = (
        dataframe[
            "condition"
        ]
        .value_counts()
    )

    for condition, count in (
        condition_counts.items()
    ):
        print(
            f"{condition:20} {count}"
        )

    print()
    print(
        "CALIBRATION CANDIDATES"
    )
    print("-" * 72)

    for (
        name,
        candidate,
    ) in calibration_candidates.items():
        print()
        print(name)

        for key, value in candidate.items():
            if isinstance(
                value,
                float,
            ):
                print(
                    f"  {key:32} "
                    f"{value:.6f}"
                )
            else:
                print(
                    f"  {key:32} "
                    f"{value}"
                )

    print()
    print("=" * 72)
    print(
        "CALIBRATION COMPLETE"
    )
    print("=" * 72)
    print()
    print(
        "IMPORTANT:"
    )
    print(
        "Candidate thresholds are evidence for review."
    )
    print(
        "They have NOT yet been installed as production rules."
    )
    print()


def main() -> None:
    """
    Main entry point.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - BUILDING QUALITY BENCHMARK"
    )
    print("=" * 72)
    print()

    catalog = load_catalog()

    representatives = select_representative_frames(
        catalog
    )

    print(
        "Representative source groups: "
        f"{len(representatives)}"
    )

    print()
    print(
        "Generating controlled image conditions..."
    )
    print()

    records = create_benchmark(
        representatives
    )

    dataframe = pd.DataFrame(
        records
    )

    print()
    print(
        "Calculating threshold candidates..."
    )

    calibration_candidates = (
        build_calibration_candidates(
            dataframe
        )
    )

    condition_summary = (
        summarize_conditions(
            dataframe
        )
    )

    save_outputs(
        dataframe=dataframe,
        calibration_candidates=(
            calibration_candidates
        ),
        condition_summary=(
            condition_summary
        ),
    )

    print_summary(
        dataframe=dataframe,
        calibration_candidates=(
            calibration_candidates
        ),
    )


if __name__ == "__main__":
    main()