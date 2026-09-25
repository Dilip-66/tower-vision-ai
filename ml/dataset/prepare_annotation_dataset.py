from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image


# ============================================================
# TowerVision AI
# Phase 1 - Prepare Annotation Dataset
# ============================================================
#
# Purpose:
#   Convert the cataloged source frames into a standardized
#   annotation-ready image dataset.
#
# IMPORTANT:
#   - data/raw is NEVER modified.
#   - MPO frames are decoded independently.
#   - All 209 catalog frames are extracted.
#   - Images are resized proportionally only when necessary.
#   - No labels are created here.
#
# Input:
#   data/raw/
#   data/reports/image_catalog.csv
#
# Output:
#   data/interim/annotation/images/
#   data/interim/annotation/annotation_manifest.csv
#   data/interim/annotation/annotation_manifest.json
#
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"

REPORT_DIR = PROJECT_ROOT / "data" / "reports"

CATALOG_PATH = (
    REPORT_DIR / "image_catalog.csv"
)

ANNOTATION_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation"
)

IMAGE_OUTPUT_DIR = (
    ANNOTATION_DIR / "images"
)

MANIFEST_CSV = (
    ANNOTATION_DIR
    / "annotation_manifest.csv"
)

MANIFEST_JSON = (
    ANNOTATION_DIR
    / "annotation_manifest.json"
)


# ------------------------------------------------------------
# Image normalization
# ------------------------------------------------------------

# Cap large images at 2048px to reduce annotation-tool memory; YOLO handles training resize.
MAX_LONG_SIDE = 2048

JPEG_QUALITY = 94


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}


def load_catalog() -> pd.DataFrame:
    """
    Load the master image catalog created earlier.
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
) -> Image.Image:
    """
    Decode one source image/frame as RGB.

    PIL is used because MPO files can contain multiple frames.
    """
    source_path = (
        PROJECT_ROOT
        / relative_path
    )

    if not source_path.exists():
        raise FileNotFoundError(
            f"Source image does not exist:\n{source_path}"
        )

    with Image.open(source_path) as image:
        image.seek(
            int(frame_index)
        )

        frame = image.convert(
            "RGB"
        ).copy()

    return frame


def resize_proportionally(
    image: Image.Image,
) -> tuple[Image.Image, bool]:
    """
    Resize an image only when its longest side exceeds the
    configured maximum.

    Aspect ratio is preserved.
    """
    width, height = image.size

    long_side = max(
        width,
        height,
    )

    if long_side <= MAX_LONG_SIDE:
        return image.copy(), False

    scale = (
        MAX_LONG_SIDE
        / long_side
    )

    new_width = max(
        1,
        int(round(width * scale)),
    )

    new_height = max(
        1,
        int(round(height * scale)),
    )

    resized = image.resize(
        (
            new_width,
            new_height,
        ),
        Image.Resampling.LANCZOS,
    )

    return resized, True


def build_output_filename(
    source_group_id: str,
    frame_index: int,
) -> str:
    """
    Build a clean, deterministic output filename.
    """
    return (
        f"{source_group_id}"
        f"_frame_{frame_index:02d}.jpg"
    )


def process_catalog_row(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Decode and standardize one catalog frame.
    """
    source_group_id = str(
        row["source_group_id"]
    )

    frame_id = str(
        row["frame_id"]
    )

    frame_index = int(
        row["frame_index"]
    )

    source_relative_path = str(
        row["source_relative_path"]
    )

    original_width = int(
        row["width"]
    )

    original_height = int(
        row["height"]
    )

    output_filename = (
        build_output_filename(
            source_group_id=source_group_id,
            frame_index=frame_index,
        )
    )

    output_path = (
        IMAGE_OUTPUT_DIR
        / output_filename
    )

    source_image = decode_frame(
        relative_path=source_relative_path,
        frame_index=frame_index,
    )

    normalized_image, resized = (
        resize_proportionally(
            source_image
        )
    )

    normalized_width, normalized_height = (
        normalized_image.size
    )

    # Ensure output directory exists (fix: was only created in save_manifest after processing)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Always save as standard RGB JPEG.
    normalized_image.save(
        output_path,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=True,
    )

    source_image.close()
    normalized_image.close()

    return {
        "frame_id": frame_id,
        "source_group_id": source_group_id,
        "source_file_name": str(
            row["source_file_name"]
        ),
        "source_relative_path": source_relative_path,
        "source_format": str(
            row["source_format"]
        ),
        "frame_index": frame_index,
        "is_mpo": (
            str(row["source_format"])
            == "MPO"
        ),
        "original_width": original_width,
        "original_height": original_height,
        "original_megapixels": round(
            (
                original_width
                * original_height
            )
            / 1_000_000,
            3,
        ),
        "processed_width": normalized_width,
        "processed_height": normalized_height,
        "was_resized": resized,
        "output_file": str(
            output_path.relative_to(
                PROJECT_ROOT
            )
        ),
        "annotation_status": "pending",
        "class_assigned": "",
        "annotation_verified": False,
    }


def build_annotation_dataset(
    catalog: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Process every valid catalog frame.
    """
    valid_catalog = catalog[
        catalog["status"] == "valid"
    ].copy()

    valid_catalog = valid_catalog.sort_values(
        [
            "source_group_id",
            "frame_index",
        ]
    )

    records: list[dict[str, Any]] = []

    total = len(
        valid_catalog
    )

    for index, (_, row) in enumerate(
        valid_catalog.iterrows(),
        start=1,
    ):
        frame_id = str(
            row["frame_id"]
        )

        print(
            f"[{index:03d}/{total:03d}] "
            f"{frame_id}"
        )

        try:
            record = process_catalog_row(
                row
            )

            records.append(
                record
            )

        except Exception as exc:
            print(
                f"    ERROR: "
                f"{type(exc).__name__}: {exc}"
            )

            records.append(
                {
                    "frame_id": frame_id,
                    "source_group_id": str(
                        row["source_group_id"]
                    ),
                    "source_file_name": str(
                        row["source_file_name"]
                    ),
                    "source_relative_path": str(
                        row["source_relative_path"]
                    ),
                    "source_format": str(
                        row["source_format"]
                    ),
                    "frame_index": int(
                        row["frame_index"]
                    ),
                    "is_mpo": (
                        str(
                            row["source_format"]
                        )
                        == "MPO"
                    ),
                    "original_width": (
                        int(
                            row["width"]
                        )
                    ),
                    "original_height": (
                        int(
                            row["height"]
                        )
                    ),
                    "original_megapixels": (
                        round(
                            (
                                int(
                                    row["width"]
                                )
                                * int(
                                    row["height"]
                                )
                            )
                            / 1_000_000,
                            3,
                        )
                    ),
                    "processed_width": None,
                    "processed_height": None,
                    "was_resized": None,
                    "output_file": "",
                    "annotation_status": (
                        "processing_error"
                    ),
                    "class_assigned": "",
                    "annotation_verified": False,
                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }
            )

    return records


def build_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build a summary of the prepared annotation dataset.
    """
    dataframe = pd.DataFrame(
        records
    )

    if dataframe.empty:
        return {
            "source_groups": 0,
            "catalog_frames": 0,
            "successful_outputs": 0,
            "failed_outputs": 0,
            "mpo_frames": 0,
            "non_mpo_frames": 0,
            "resized_frames": 0,
        }

    successful = dataframe[
        dataframe[
            "annotation_status"
        ]
        == "pending"
    ]

    failed = dataframe[
        dataframe[
            "annotation_status"
        ]
        != "pending"
    ]

    source_groups = int(
        dataframe[
            "source_group_id"
        ].nunique()
    )

    mpo_frames = int(
        dataframe[
            "is_mpo"
        ]
        .fillna(False)
        .sum()
    )

    return {
        "source_groups": source_groups,
        "catalog_frames": int(
            len(dataframe)
        ),
        "successful_outputs": int(
            len(successful)
        ),
        "failed_outputs": int(
            len(failed)
        ),
        "mpo_frames": mpo_frames,
        "non_mpo_frames": int(
            len(dataframe)
            - mpo_frames
        ),
        "resized_frames": int(
            dataframe[
                "was_resized"
            ]
            .fillna(False)
            .sum()
        ),
        "annotation_status": (
            "pending_annotation"
        ),
    }


def save_manifest(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """
    Save annotation manifest as CSV and JSON.
    """
    ANNOTATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    IMAGE_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = pd.DataFrame(
        records
    )

    dataframe.to_csv(
        MANIFEST_CSV,
        index=False,
        encoding="utf-8",
    )

    payload = {
        "summary": summary,
        "records": records,
    }

    with MANIFEST_JSON.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(
        f"Manifest CSV  : {MANIFEST_CSV}"
    )

    print(
        f"Manifest JSON : {MANIFEST_JSON}"
    )


def print_summary(
    summary: dict[str, Any],
) -> None:
    """
    Print the preparation summary.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - ANNOTATION DATASET PREPARATION"
    )
    print("=" * 72)

    print()
    print(
        f"Source groups       : "
        f"{summary['source_groups']}"
    )

    print(
        f"Catalog frames      : "
        f"{summary['catalog_frames']}"
    )

    print(
        f"Successful outputs  : "
        f"{summary['successful_outputs']}"
    )

    print(
        f"Failed outputs      : "
        f"{summary['failed_outputs']}"
    )

    print(
        f"MPO frames          : "
        f"{summary['mpo_frames']}"
    )

    print(
        f"Non-MPO frames      : "
        f"{summary['non_mpo_frames']}"
    )

    print(
        f"Resized frames      : "
        f"{summary['resized_frames']}"
    )

    print()
    print(
        "Annotation status   : "
        "PENDING"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "No annotations were created."
    )

    print(
        "No raw images were modified."
    )

    print(
        "Source groups will be preserved for leakage-safe splitting."
    )

    print()
    print("=" * 72)
    print(
        "ANNOTATION DATASET PREPARATION COMPLETE"
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
        "TOWERVISION AI - PREPARING ANNOTATION DATASET"
    )
    print("=" * 72)
    print()

    catalog = load_catalog()

    print(
        f"Catalog rows: {len(catalog)}"
    )

    # Ensure annotation output directories exist before extraction
    ANNOTATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    IMAGE_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "Extracting and standardizing frames..."
    )
    print()

    records = build_annotation_dataset(
        catalog
    )

    summary = build_summary(
        records
    )

    save_manifest(
        records=records,
        summary=summary,
    )

    print_summary(
        summary
    )


if __name__ == "__main__":
    main()