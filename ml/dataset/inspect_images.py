from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import pandas as pd
from PIL import Image, UnidentifiedImageError


# ============================================================
# TowerVision AI
# Phase 1 - Image Inspection
# ============================================================
#
# Purpose:
#   Perform a deeper, read-only inspection of the organizer's
#   raw images.
#
# Input:
#   data/raw/
#
# Outputs:
#   data/reports/image_inspection.csv
#   data/reports/image_inspection.json
#
# This script NEVER modifies the raw images.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}


def calculate_sha256(
    file_path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """
    Calculate the SHA-256 hash of a file.
    """
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def get_exif_summary(image: Image.Image) -> dict[str, Any]:
    """
    Extract a small set of useful EXIF metadata.

    We intentionally avoid dumping all EXIF data into the report.
    """
    result: dict[str, Any] = {
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "orientation": None,
        "datetime_original": None,
    }

    try:
        exif = image.getexif()

        if not exif:
            return result

        # Standard EXIF tag IDs.
        result["camera_make"] = exif.get(271)
        result["camera_model"] = exif.get(272)
        result["software"] = exif.get(305)
        result["orientation"] = exif.get(274)
        result["datetime_original"] = exif.get(36867)

    except Exception:
        pass

    return result


def inspect_pillow(
    file_path: Path,
) -> dict[str, Any]:
    """
    Inspect the image using Pillow.

    Also attempts to determine whether an MPO image contains
    multiple frames.
    """
    with Image.open(file_path) as image:
        width, height = image.size
        image_format = image.format
        mode = image.mode

        frame_count = 1

        try:
            frame_count = getattr(image, "n_frames", 1)
        except Exception:
            frame_count = 1

        exif = get_exif_summary(image)

    return {
        "width": width,
        "height": height,
        "format": image_format,
        "mode": mode,
        "frame_count": frame_count,
        **exif,
    }


def inspect_opencv(
    file_path: Path,
) -> dict[str, Any]:
    """
    Verify that OpenCV can decode the image.

    OpenCV is important because it will later be used for
    preprocessing and image-quality analysis.
    """
    image = cv2.imread(
        str(file_path),
        cv2.IMREAD_UNCHANGED,
    )

    if image is None:
        raise ValueError(
            "OpenCV could not decode the image."
        )

    shape = image.shape

    if len(shape) == 2:
        channels = 1
    else:
        channels = shape[2]

    return {
        "opencv_height": int(shape[0]),
        "opencv_width": int(shape[1]),
        "opencv_channels": channels,
    }


def classify_resolution(
    width: int,
    height: int,
) -> str:
    """
    Give a basic resolution category.

    This is descriptive only.
    It is NOT a quality decision.
    """
    pixels = width * height

    if pixels < 100_000:
        return "very_low"

    if pixels < 500_000:
        return "low"

    if pixels < 2_000_000:
        return "medium"

    if pixels < 10_000_000:
        return "high"

    return "very_high"


def inspect_file(
    file_path: Path,
) -> dict[str, Any]:
    """
    Inspect one image and return a complete record.
    """
    file_size_bytes = file_path.stat().st_size
    file_hash = calculate_sha256(file_path)

    record: dict[str, Any] = {
        "file_name": file_path.name,
        "relative_path": str(
            file_path.relative_to(PROJECT_ROOT)
        ),
        "extension": file_path.suffix.lower(),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(
            file_size_bytes / (1024 * 1024),
            4,
        ),
        "sha256": file_hash,
        "status": "valid",
        "error": "",
        "width": None,
        "height": None,
        "format": None,
        "mode": None,
        "frame_count": None,
        "aspect_ratio": None,
        "megapixels": None,
        "resolution_category": None,
        "opencv_width": None,
        "opencv_height": None,
        "opencv_channels": None,
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "orientation": None,
        "datetime_original": None,
    }

    try:
        pillow_info = inspect_pillow(file_path)
        opencv_info = inspect_opencv(file_path)

        width = pillow_info["width"]
        height = pillow_info["height"]

        record.update(
            {
                "width": width,
                "height": height,
                "format": pillow_info["format"],
                "mode": pillow_info["mode"],
                "frame_count": pillow_info["frame_count"],
                "opencv_width": opencv_info["opencv_width"],
                "opencv_height": opencv_info["opencv_height"],
                "opencv_channels": opencv_info["opencv_channels"],
                "camera_make": pillow_info["camera_make"],
                "camera_model": pillow_info["camera_model"],
                "software": pillow_info["software"],
                "orientation": pillow_info["orientation"],
                "datetime_original": pillow_info[
                    "datetime_original"
                ],
            }
        )

        if height > 0:
            record["aspect_ratio"] = round(
                width / height,
                4,
            )

        record["megapixels"] = round(
            (width * height) / 1_000_000,
            3,
        )

        record["resolution_category"] = classify_resolution(
            width,
            height,
        )

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        cv2.error,
    ) as exc:
        record["status"] = "unreadable"
        record["error"] = str(exc)

    except Exception as exc:
        record["status"] = "inspection_error"
        record["error"] = (
            f"{type(exc).__name__}: {exc}"
        )

    return record


def find_image_files() -> list[Path]:
    """
    Find all supported image files under data/raw.
    """
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw dataset directory does not exist:\n{RAW_DIR}"
        )

    return sorted(
        path
        for path in RAW_DIR.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    )


def build_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build a summary suitable for JSON reporting.
    """
    valid_records = [
        record
        for record in records
        if record["status"] == "valid"
    ]

    unreadable_records = [
        record
        for record in records
        if record["status"] != "valid"
    ]

    formats: dict[str, int] = {}

    for record in valid_records:
        image_format = str(record["format"])

        formats[image_format] = (
            formats.get(image_format, 0) + 1
        )

    resolution_categories: dict[str, int] = {}

    for record in valid_records:
        category = str(
            record["resolution_category"]
        )

        resolution_categories[category] = (
            resolution_categories.get(category, 0) + 1
        )

    mpo_records = [
        record
        for record in valid_records
        if record["format"] == "MPO"
    ]

    multi_frame_records = [
        record
        for record in valid_records
        if (
            record["frame_count"] is not None
            and record["frame_count"] > 1
        )
    ]

    hashes: dict[str, list[str]] = {}

    for record in valid_records:
        hashes.setdefault(
            record["sha256"],
            [],
        ).append(record["file_name"])

    exact_duplicate_groups = [
        files
        for files in hashes.values()
        if len(files) > 1
    ]

    summary = {
        "raw_dataset": str(RAW_DIR),
        "total_images": len(records),
        "valid_images": len(valid_records),
        "unreadable_images": len(unreadable_records),
        "formats": formats,
        "resolution_categories": resolution_categories,
        "mpo_images": len(mpo_records),
        "multi_frame_images": len(
            multi_frame_records
        ),
        "exact_duplicate_groups": len(
            exact_duplicate_groups
        ),
        "exact_duplicate_files": sum(
            len(group)
            for group in exact_duplicate_groups
        ),
        "exact_duplicate_groups_detail": (
            exact_duplicate_groups
        ),
        "unreadable_files": [
            {
                "file_name": record["file_name"],
                "error": record["error"],
            }
            for record in unreadable_records
        ],
    }

    return summary


def save_reports(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """
    Save CSV and JSON reports.
    """
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = REPORT_DIR / "image_inspection.csv"
    json_path = REPORT_DIR / "image_inspection.json"

    dataframe = pd.DataFrame(records)

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

    print()
    print(f"CSV report : {csv_path}")
    print(f"JSON report: {json_path}")


def print_report(
    summary: dict[str, Any],
) -> None:
    """
    Print a readable summary to the terminal.
    """
    print()
    print("=" * 72)
    print("TOWERVISION AI - IMAGE INSPECTION")
    print("=" * 72)

    print(
        f"Total images          : "
        f"{summary['total_images']}"
    )

    print(
        f"Valid images          : "
        f"{summary['valid_images']}"
    )

    print(
        f"Unreadable images     : "
        f"{summary['unreadable_images']}"
    )

    print()
    print("FORMATS")
    print("-" * 72)

    for name, count in summary["formats"].items():
        print(f"{name:25} {count}")

    print()
    print("RESOLUTION CATEGORIES")
    print("-" * 72)

    for name, count in (
        summary["resolution_categories"].items()
    ):
        print(f"{name:25} {count}")

    print()
    print("MPO ANALYSIS")
    print("-" * 72)

    print(
        f"MPO images            : "
        f"{summary['mpo_images']}"
    )

    print(
        f"Multi-frame images    : "
        f"{summary['multi_frame_images']}"
    )

    print()
    print("EXACT DUPLICATES")
    print("-" * 72)

    print(
        f"Duplicate groups      : "
        f"{summary['exact_duplicate_groups']}"
    )

    print(
        f"Files involved        : "
        f"{summary['exact_duplicate_files']}"
    )

    if summary["exact_duplicate_groups_detail"]:
        print()

        for index, group in enumerate(
            summary["exact_duplicate_groups_detail"],
            start=1,
        ):
            print(f"Group {index}:")

            for file_name in group:
                print(f"  - {file_name}")

    print()
    print("=" * 72)
    print("DETAILED IMAGE INSPECTION COMPLETE")
    print("=" * 72)
    print()


def main() -> None:
    """
    Main entry point.
    """
    print()
    print("Starting TowerVision image inspection...")
    print(f"Scanning: {RAW_DIR}")
    print()

    image_files = find_image_files()

    print(
        f"Found {len(image_files)} image files."
    )

    records = [
        inspect_file(file_path)
        for file_path in image_files
    ]

    summary = build_summary(records)

    save_reports(
        records=records,
        summary=summary,
    )

    print_report(summary)


if __name__ == "__main__":
    main()