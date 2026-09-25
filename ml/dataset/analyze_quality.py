from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# TowerVision AI
# Phase 1 - Image Quality Analysis
# ============================================================
#
# Purpose:
#   Measure image-quality characteristics across every frame
#   in the master image catalog.
#
# Important:
#   This script ANALYZES only.
#   It does NOT reject, delete, rename, resize, or modify
#   any source image.
#
# Quality dimensions:
#   - Resolution
#   - Sharpness / blur
#   - Mean brightness
#   - Brightness standard deviation
#   - Dark pixel percentage
#   - Bright pixel percentage
#   - Dynamic range
#
# Input:
#   data/raw/
#   data/reports/image_catalog.csv
#
# Outputs:
#   data/reports/quality_analysis.csv
#   data/reports/quality_analysis.json
#
#   data/interim/
#       quality_blur_low.jpg
#       quality_darkest.jpg
#       quality_brightest.jpg
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"

CATALOG_PATH = REPORT_DIR / "image_catalog.csv"

# Processing resolution for quality metrics.
# We measure normalized images so very large photographs do not
# dominate computation time.
ANALYSIS_WIDTH = 1024
ANALYSIS_HEIGHT = 1024

# Luminance thresholds for descriptive stats (not final thresholds).
DARK_PIXEL_THRESHOLD = 32
BRIGHT_PIXEL_THRESHOLD = 223

# Contact sheet settings.
CONTACT_COLUMNS = 4
THUMBNAIL_SIZE = (320, 240)
LABEL_HEIGHT = 58

BACKGROUND = (245, 245, 245)
TEXT_COLOR = (20, 20, 20)
BORDER_COLOR = (170, 170, 170)


def load_catalog() -> pd.DataFrame:
    """
    Load the master image catalog generated during Phase 1.
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
        "source_file_name",
        "source_relative_path",
        "frame_index",
        "source_format",
        "width",
        "height",
        "status",
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


def decode_frame(
    relative_path: str,
    frame_index: int,
) -> np.ndarray:
    """
    Decode one frame as an OpenCV grayscale image.

    PIL is used because the dataset contains MPO files with
    multiple frames.
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
    Resize the image while keeping the aspect ratio.
    """
    height, width = grayscale.shape[:2]

    if width <= 0 or height <= 0:
        raise ValueError(
            "Image has invalid dimensions."
        )

    scale = min(
        ANALYSIS_WIDTH / width,
        ANALYSIS_HEIGHT / height,
        1.0,
    )

    if scale == 1.0:
        return grayscale

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
    Calculate variance of the Laplacian.

    Higher values generally indicate more high-frequency image
    detail. Lower values can indicate blur.

    This metric alone is NOT a final quality decision.
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
    Calculate brightness and contrast-related statistics.
    """
    pixels = grayscale.astype(
        np.float32
    )

    mean = float(
        np.mean(pixels)
    )

    standard_deviation = float(
        np.std(pixels)
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

    dark_percentage = float(
        np.mean(
            pixels <= DARK_PIXEL_THRESHOLD
        )
        * 100.0
    )

    bright_percentage = float(
        np.mean(
            pixels >= BRIGHT_PIXEL_THRESHOLD
        )
        * 100.0
    )

    dynamic_range = float(
        percentiles[5]
        - percentiles[1]
    )

    return {
        "mean_brightness": mean,
        "brightness_std": standard_deviation,
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
        "dark_pixel_percentage": dark_percentage,
        "bright_pixel_percentage": bright_percentage,
        "dynamic_range": dynamic_range,
    }


def calculate_texture_measure(
    grayscale: np.ndarray,
) -> float:
    """
    Measure local intensity variation using image gradients.

    This is a supplementary signal that may help distinguish
    extremely flat images from detailed ones.
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

    gradient_magnitude = cv2.magnitude(
        sobel_x,
        sobel_y,
    )

    return float(
        np.mean(
            gradient_magnitude
        )
    )


def classify_descriptive_quality(
    row: dict[str, Any],
) -> str:
    """
    Assign a descriptive category using percentile-relative
    measurements.

    These categories are intentionally conservative and are
    NOT used by the eventual production quality gate.
    They exist to help us inspect the dataset.
    """
    sharpness = row["sharpness_laplacian"]

    mean_brightness = row[
        "mean_brightness"
    ]

    dark_percentage = row[
        "dark_pixel_percentage"
    ]

    bright_percentage = row[
        "bright_pixel_percentage"
    ]

    dynamic_range = row[
        "dynamic_range"
    ]

    issues: list[str] = []

    if sharpness < 20:
        issues.append("very_low_sharpness")

    if mean_brightness < 40:
        issues.append("dark_image_candidate")

    if mean_brightness > 220:
        issues.append("bright_image_candidate")

    if dark_percentage > 35:
        issues.append("high_dark_pixel_ratio")

    if bright_percentage > 35:
        issues.append("high_bright_pixel_ratio")

    if dynamic_range < 40:
        issues.append("low_dynamic_range")

    if not issues:
        return "no_obvious_quality_issue"

    return ";".join(
        issues
    )


def analyze_frame(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Analyze one catalog frame.
    """
    relative_path = str(
        row["source_relative_path"]
    )

    frame_index = int(
        row["frame_index"]
    )

    grayscale = decode_frame(
        relative_path=relative_path,
        frame_index=frame_index,
    )

    analyzed = resize_for_analysis(
        grayscale
    )

    quality = calculate_brightness_metrics(
        analyzed
    )

    sharpness = calculate_sharpness(
        analyzed
    )

    texture = calculate_texture_measure(
        analyzed
    )

    height, width = analyzed.shape[:2]

    result: dict[str, Any] = {
        "frame_id": row["frame_id"],
        "source_group_id": row[
            "source_group_id"
        ],
        "source_file_name": row[
            "source_file_name"
        ],
        "source_relative_path": relative_path,
        "source_format": row[
            "source_format"
        ],
        "frame_index": frame_index,
        "original_width": int(
            row["width"]
        ),
        "original_height": int(
            row["height"]
        ),
        "original_megapixels": round(
            (
                int(row["width"])
                * int(row["height"])
            )
            / 1_000_000,
            3,
        ),
        "analysis_width": width,
        "analysis_height": height,
        "sharpness_laplacian": round(
            sharpness,
            6,
        ),
        "gradient_texture_mean": round(
            texture,
            6,
        ),
        **{
            key: round(
                value,
                6,
            )
            for key, value in quality.items()
        },
    }

    result[
        "descriptive_quality_flags"
    ] = classify_descriptive_quality(
        result
    )

    return result


def analyze_all_frames(
    catalog: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Analyze every valid frame in the catalog.
    """
    valid_catalog = catalog[
        catalog["status"] == "valid"
    ].copy()

    records: list[dict[str, Any]] = []

    total = len(valid_catalog)

    for index, (_, row) in enumerate(
        valid_catalog.iterrows(),
        start=1,
    ):
        print(
            f"[{index:03d}/{total:03d}] "
            f"{row['frame_id']}"
        )

        try:
            record = analyze_frame(
                row
            )

            records.append(
                record
            )

        except Exception as exc:
            records.append(
                {
                    "frame_id": row[
                        "frame_id"
                    ],
                    "source_group_id": row[
                        "source_group_id"
                    ],
                    "source_file_name": row[
                        "source_file_name"
                    ],
                    "source_relative_path": row[
                        "source_relative_path"
                    ],
                    "source_format": row[
                        "source_format"
                    ],
                    "frame_index": int(
                        row["frame_index"]
                    ),
                    "status": (
                        "error: "
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }
            )

    return records


def build_summary(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Build numeric dataset statistics.
    """
    numeric_columns = [
        "sharpness_laplacian",
        "gradient_texture_mean",
        "mean_brightness",
        "brightness_std",
        "dark_pixel_percentage",
        "bright_pixel_percentage",
        "dynamic_range",
        "original_megapixels",
    ]

    summary: dict[str, Any] = {
        "frames_analyzed": int(
            len(dataframe)
        )
    }

    if dataframe.empty:
        return summary

    summary["quality_metrics"] = {}

    for column in numeric_columns:
        if column not in dataframe.columns:
            continue

        values = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).dropna()

        if values.empty:
            continue

        summary["quality_metrics"][
            column
        ] = {
            "minimum": round(
                float(values.min()),
                6,
            ),
            "p05": round(
                float(values.quantile(0.05)),
                6,
            ),
            "p25": round(
                float(values.quantile(0.25)),
                6,
            ),
            "median": round(
                float(values.median()),
                6,
            ),
            "p75": round(
                float(values.quantile(0.75)),
                6,
            ),
            "p95": round(
                float(values.quantile(0.95)),
                6,
            ),
            "maximum": round(
                float(values.max()),
                6,
            ),
            "mean": round(
                float(values.mean()),
                6,
            ),
            "std": round(
                float(values.std()),
                6,
            ),
        }

    if "descriptive_quality_flags" in dataframe.columns:
        flags = (
            dataframe[
                "descriptive_quality_flags"
            ]
            .fillna("unknown")
            .value_counts()
            .to_dict()
        )

        summary[
            "descriptive_flag_distribution"
        ] = {
            str(key): int(value)
            for key, value in flags.items()
        }

    return summary


def get_extreme_rows(
    dataframe: pd.DataFrame,
    metric: str,
    ascending: bool,
    count: int = 12,
) -> pd.DataFrame:
    """
    Get the most extreme valid rows for a metric.
    """
    valid = dataframe[
        dataframe[metric].notna()
    ].copy()

    return (
        valid.sort_values(
            metric,
            ascending=ascending,
        )
        .head(count)
        .reset_index(drop=True)
    )


def load_frame_rgb(
    row: pd.Series,
) -> Image.Image:
    """
    Decode one catalog frame into a PIL RGB image.
    """
    path = (
        PROJECT_ROOT
        / str(row["source_relative_path"])
    )

    with Image.open(path) as image:
        image.seek(
            int(row["frame_index"])
        )

        return image.convert(
            "RGB"
        ).copy()


def create_contact_sheet(
    dataframe: pd.DataFrame,
    metric: str,
    ascending: bool,
    output_path: Path,
    title: str,
    count: int = 12,
) -> None:
    """
    Create a contact sheet for extreme quality cases.
    """
    rows = get_extreme_rows(
        dataframe=dataframe,
        metric=metric,
        ascending=ascending,
        count=count,
    )

    if rows.empty:
        return

    cell_width = THUMBNAIL_SIZE[0]
    cell_height = (
        THUMBNAIL_SIZE[1]
        + LABEL_HEIGHT
    )

    sheet_rows = math.ceil(
        len(rows)
        / CONTACT_COLUMNS
    )

    sheet = Image.new(
        "RGB",
        (
            cell_width
            * CONTACT_COLUMNS,
            cell_height
            * sheet_rows,
        ),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for index, (_, row) in enumerate(
        rows.iterrows()
    ):
        column = (
            index
            % CONTACT_COLUMNS
        )

        row_number = (
            index
            // CONTACT_COLUMNS
        )

        x = column * cell_width
        y = row_number * cell_height

        try:
            image = load_frame_rgb(
                row
            )

            image.thumbnail(
                THUMBNAIL_SIZE,
                Image.Resampling.LANCZOS,
            )

            paste_x = x + (
                cell_width
                - image.width
            ) // 2

            paste_y = y + (
                THUMBNAIL_SIZE[1]
                - image.height
            ) // 2

            sheet.paste(
                image,
                (
                    paste_x,
                    paste_y,
                ),
            )

            image.close()

            draw.rectangle(
                [
                    x + 3,
                    y + 3,
                    x + cell_width - 3,
                    y + THUMBNAIL_SIZE[1] - 3,
                ],
                outline=BORDER_COLOR,
                width=1,
            )

            metric_value = row[
                metric
            ]

            label = (
                f"{row['frame_id']}\n"
                f"{metric}: "
                f"{metric_value:.2f}"
            )

            draw.text(
                (
                    x + 7,
                    y + THUMBNAIL_SIZE[1] + 6,
                ),
                label,
                fill=TEXT_COLOR,
                font=font,
            )

        except Exception as exc:
            draw.text(
                (
                    x + 8,
                    y + 8,
                ),
                (
                    f"Unable to load\n"
                    f"{row['frame_id']}\n"
                    f"{type(exc).__name__}"
                ),
                fill=TEXT_COLOR,
                font=font,
            )

    # Contact sheet remains image-focused.
    sheet.save(
        output_path,
        quality=92,
    )

    sheet.close()


def save_outputs(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """
    Save the complete quality report.
    """
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    INTERIM_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = pd.DataFrame(
        records
    )

    csv_path = (
        REPORT_DIR
        / "quality_analysis.csv"
    )

    json_path = (
        REPORT_DIR
        / "quality_analysis.json"
    )

    dataframe.to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    payload = {
        "summary": summary,
        "records": records,
    }

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )

    create_contact_sheet(
        dataframe=dataframe,
        metric="sharpness_laplacian",
        ascending=True,
        output_path=(
            INTERIM_DIR
            / "quality_blur_low.jpg"
        ),
        title="Lowest Sharpness",
    )

    create_contact_sheet(
        dataframe=dataframe,
        metric="mean_brightness",
        ascending=True,
        output_path=(
            INTERIM_DIR
            / "quality_darkest.jpg"
        ),
        title="Darkest Images",
    )

    create_contact_sheet(
        dataframe=dataframe,
        metric="mean_brightness",
        ascending=False,
        output_path=(
            INTERIM_DIR
            / "quality_brightest.jpg"
        ),
        title="Brightest Images",
    )

    print()
    print(
        f"CSV report : {csv_path}"
    )

    print(
        f"JSON report: {json_path}"
    )

    print(
        "Blur review sheet    : "
        f"{INTERIM_DIR / 'quality_blur_low.jpg'}"
    )

    print(
        "Dark review sheet    : "
        f"{INTERIM_DIR / 'quality_darkest.jpg'}"
    )

    print(
        "Bright review sheet  : "
        f"{INTERIM_DIR / 'quality_brightest.jpg'}"
    )


def print_summary(
    summary: dict[str, Any],
) -> None:
    """
    Print the quality analysis summary.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - IMAGE QUALITY ANALYSIS"
    )
    print("=" * 72)

    print(
        f"Frames analyzed : "
        f"{summary['frames_analyzed']}"
    )

    print()
    print("QUALITY METRIC DISTRIBUTIONS")
    print("-" * 72)

    metrics = summary.get(
        "quality_metrics",
        {},
    )

    for metric, values in metrics.items():
        print()
        print(metric)

        print(
            f"  minimum : {values['minimum']}"
        )

        print(
            f"  p05     : {values['p05']}"
        )

        print(
            f"  p25     : {values['p25']}"
        )

        print(
            f"  median  : {values['median']}"
        )

        print(
            f"  p75     : {values['p75']}"
        )

        print(
            f"  p95     : {values['p95']}"
        )

        print(
            f"  maximum : {values['maximum']}"
        )

    print()
    print("DESCRIPTIVE FLAGS")
    print("-" * 72)

    flags = summary.get(
        "descriptive_flag_distribution",
        {},
    )

    if flags:
        for flag, count in flags.items():
            print(
                f"{flag:35} {count}"
            )
    else:
        print("No flags available.")

    print()
    print("=" * 72)
    print(
        "QUALITY ANALYSIS COMPLETE"
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
        "TOWERVISION AI - PHASE 1 QUALITY ANALYSIS"
    )
    print("=" * 72)
    print()

    catalog = load_catalog()

    print(
        f"Catalog rows found: {len(catalog)}"
    )

    print(
        "Analyzing image quality..."
    )
    print()

    records = analyze_all_frames(
        catalog
    )

    dataframe = pd.DataFrame(
        records
    )

    # Keep only records that have the main quality metrics.
    valid_quality = dataframe[
        dataframe[
            "sharpness_laplacian"
        ].notna()
    ].copy()

    summary = build_summary(
        valid_quality
    )

    save_outputs(
        records=records,
        summary=summary,
    )

    print_summary(
        summary
    )


if __name__ == "__main__":
    main()