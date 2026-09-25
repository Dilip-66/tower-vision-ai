from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import pandas as pd
from PIL import Image, UnidentifiedImageError


# ============================================================
# TowerVision AI - Phase 1 Dataset Audit
# ============================================================
#
# Purpose:
#   Perform a read-only audit of the organizer-provided raw
#   dataset before any preprocessing, resizing, labeling,
#   conversion, or training.
#
# Input:
#   dataset/raw/
#
# Output:
#   dataset/reports/
#       dataset_audit.csv
#       dataset_audit.json
#
# Important:
#   This script NEVER modifies the raw dataset.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "dataset" / "raw"
REPORT_DIR = PROJECT_ROOT / "dataset" / "reports"

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

ANNOTATION_EXTENSIONS = {
    ".txt",
    ".xml",
    ".json",
    ".csv",
}


def calculate_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Hashes allow us to identify exact duplicate files without
    modifying or interpreting their contents.
    """
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def inspect_with_pillow(file_path: Path) -> dict[str, Any]:
    """
    Read image metadata using Pillow.

    Returns width, height, format and mode.
    """
    with Image.open(file_path) as image:
        image.verify()

    with Image.open(file_path) as image:
        width, height = image.size
        image_format = image.format
        mode = image.mode

    return {
        "width": width,
        "height": height,
        "format": image_format,
        "mode": mode,
    }


def inspect_with_opencv(file_path: Path) -> dict[str, Any]:
    """
    Load the image using OpenCV to verify that the file is also
    decodable through the library we will later use for image
    processing and quality analysis.
    """
    image = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)

    if image is None:
        raise ValueError("OpenCV could not decode the image.")

    return {
        "opencv_shape": tuple(image.shape),
    }


def classify_file(file_path: Path) -> str:
    """
    Classify files into image, annotation-like, or other.
    """
    extension = file_path.suffix.lower()

    if extension in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"

    if extension in ANNOTATION_EXTENSIONS:
        return "annotation_candidate"

    return "other"


def build_image_record(file_path: Path) -> dict[str, Any]:
    """
    Build a complete audit record for one image.
    """
    file_size_bytes = file_path.stat().st_size
    sha256 = calculate_sha256(file_path)

    record: dict[str, Any] = {
        "file_name": file_path.name,
        "relative_path": str(file_path.relative_to(PROJECT_ROOT)),
        "extension": file_path.suffix.lower(),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 4),
        "sha256": sha256,
        "status": "valid",
        "error": "",
        "width": None,
        "height": None,
        "format": None,
        "mode": None,
        "aspect_ratio": None,
        "megapixels": None,
    }

    try:
        pillow_info = inspect_with_pillow(file_path)

        record["width"] = pillow_info["width"]
        record["height"] = pillow_info["height"]
        record["format"] = pillow_info["format"]
        record["mode"] = pillow_info["mode"]

        width = pillow_info["width"]
        height = pillow_info["height"]

        if height > 0:
            record["aspect_ratio"] = round(width / height, 4)

        record["megapixels"] = round((width * height) / 1_000_000, 3)

        # Verify decoding through OpenCV as well.
        inspect_with_opencv(file_path)

    except (UnidentifiedImageError, OSError, ValueError, cv2.error) as exc:
        record["status"] = "corrupt_or_unreadable"
        record["error"] = str(exc)

    except Exception as exc:
        record["status"] = "audit_error"
        record["error"] = f"{type(exc).__name__}: {exc}"

    return record


def find_files() -> list[Path]:
    """
    Recursively find every file in dataset/raw.
    """
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw dataset directory does not exist:\n{RAW_DIR}"
        )

    return sorted(
        path for path in RAW_DIR.rglob("*")
        if path.is_file()
    )


def summarize(records: list[dict[str, Any]], all_files: list[Path]) -> dict[str, Any]:
    """
    Build a machine-readable dataset summary.
    """
    file_types = Counter(
        classify_file(path)
        for path in all_files
    )

    image_records = [
        record
        for record in records
        if record["extension"] in SUPPORTED_IMAGE_EXTENSIONS
    ]

    valid_images = [
        record
        for record in image_records
        if record["status"] == "valid"
    ]

    corrupt_images = [
        record
        for record in image_records
        if record["status"] != "valid"
    ]

    sha_counts = Counter(
        record["sha256"]
        for record in valid_images
    )

    duplicate_groups = [
        {
            "sha256": sha,
            "count": count,
            "files": [
                record["file_name"]
                for record in valid_images
                if record["sha256"] == sha
            ],
        }
        for sha, count in sha_counts.items()
        if count > 1
    ]

    widths = [
        record["width"]
        for record in valid_images
        if record["width"] is not None
    ]

    heights = [
        record["height"]
        for record in valid_images
        if record["height"] is not None
    ]

    file_sizes = [
        record["file_size_mb"]
        for record in valid_images
    ]

    aspect_ratios = [
        record["aspect_ratio"]
        for record in valid_images
        if record["aspect_ratio"] is not None
    ]

    megapixels = [
        record["megapixels"]
        for record in valid_images
        if record["megapixels"] is not None
    ]

    formats = Counter(
        str(record["format"])
        for record in valid_images
    )

    summary = {
        "dataset_path": str(RAW_DIR),
        "total_files": len(all_files),
        "total_images": len(image_records),
        "valid_images": len(valid_images),
        "invalid_images": len(corrupt_images),
        "annotation_candidate_files": file_types["annotation_candidate"],
        "other_files": file_types["other"],
        "image_formats": dict(formats),
        "file_type_counts": dict(file_types),
        "exact_duplicate_groups": len(duplicate_groups),
        "exact_duplicate_files": sum(
            group["count"]
            for group in duplicate_groups
        ),
        "dimensions": {
            "min_width": min(widths) if widths else None,
            "max_width": max(widths) if widths else None,
            "average_width": round(sum(widths) / len(widths), 2)
            if widths
            else None,
            "min_height": min(heights) if heights else None,
            "max_height": max(heights) if heights else None,
            "average_height": round(sum(heights) / len(heights), 2)
            if heights
            else None,
        },
        "file_size_mb": {
            "min": round(min(file_sizes), 4)
            if file_sizes
            else None,
            "max": round(max(file_sizes), 4)
            if file_sizes
            else None,
            "average": round(sum(file_sizes) / len(file_sizes), 4)
            if file_sizes
            else None,
            "total": round(sum(file_sizes), 4)
            if file_sizes
            else None,
        },
        "aspect_ratio": {
            "min": round(min(aspect_ratios), 4)
            if aspect_ratios
            else None,
            "max": round(max(aspect_ratios), 4)
            if aspect_ratios
            else None,
            "average": round(sum(aspect_ratios) / len(aspect_ratios), 4)
            if aspect_ratios
            else None,
        },
        "megapixels": {
            "min": round(min(megapixels), 3)
            if megapixels
            else None,
            "max": round(max(megapixels), 3)
            if megapixels
            else None,
            "average": round(sum(megapixels) / len(megapixels), 3)
            if megapixels
            else None,
        },
        "duplicate_groups": duplicate_groups,
        "corrupt_images": [
            {
                "file_name": record["file_name"],
                "error": record["error"],
            }
            for record in corrupt_images
        ],
    }

    return summary


def print_console_report(
    summary: dict[str, Any],
    records: list[dict[str, Any]],
) -> None:
    """
    Print a human-readable audit report to the terminal.
    """
    print()
    print("=" * 72)
    print("TOWERVISION AI - PHASE 1 DATASET AUDIT")
    print("=" * 72)

    print(f"Raw dataset : {summary['dataset_path']}")
    print(f"Total files : {summary['total_files']}")
    print(f"Images      : {summary['total_images']}")
    print(f"Valid       : {summary['valid_images']}")
    print(f"Invalid     : {summary['invalid_images']}")

    print()
    print("FILE TYPES")
    print("-" * 72)

    for file_type, count in summary["file_type_counts"].items():
        print(f"{file_type:25} {count}")

    print()
    print("IMAGE FORMATS")
    print("-" * 72)

    if summary["image_formats"]:
        for image_format, count in summary["image_formats"].items():
            print(f"{image_format:25} {count}")
    else:
        print("No valid images found.")

    print()
    print("DIMENSIONS")
    print("-" * 72)

    dimensions = summary["dimensions"]

    print(f"Minimum width          : {dimensions['min_width']}")
    print(f"Maximum width          : {dimensions['max_width']}")
    print(f"Average width          : {dimensions['average_width']}")
    print(f"Minimum height         : {dimensions['min_height']}")
    print(f"Maximum height         : {dimensions['max_height']}")
    print(f"Average height         : {dimensions['average_height']}")

    print()
    print("FILE SIZE")
    print("-" * 72)

    sizes = summary["file_size_mb"]

    print(f"Minimum MB             : {sizes['min']}")
    print(f"Maximum MB             : {sizes['max']}")
    print(f"Average MB             : {sizes['average']}")
    print(f"Total MB               : {sizes['total']}")

    print()
    print("ASPECT RATIO")
    print("-" * 72)

    ratios = summary["aspect_ratio"]

    print(f"Minimum                : {ratios['min']}")
    print(f"Maximum                : {ratios['max']}")
    print(f"Average                : {ratios['average']}")

    print()
    print("DUPLICATES")
    print("-" * 72)

    print(
        f"Exact duplicate groups : "
        f"{summary['exact_duplicate_groups']}"
    )

    print(
        f"Files in duplicate groups: "
        f"{summary['exact_duplicate_files']}"
    )

    if summary["duplicate_groups"]:
        print()
        for index, group in enumerate(
            summary["duplicate_groups"],
            start=1,
        ):
            print(f"Group {index}:")
            for file_name in group["files"]:
                print(f"  - {file_name}")

    print()
    print("ANNOTATION CANDIDATES")
    print("-" * 72)

    annotation_count = summary["annotation_candidate_files"]

    if annotation_count == 0:
        print(
            "No annotation-like files were found in dataset/raw."
        )
    else:
        print(
            f"Found {annotation_count} annotation-like file(s)."
        )

    print()
    print("CORRUPT / UNREADABLE IMAGES")
    print("-" * 72)

    if summary["corrupt_images"]:
        for image in summary["corrupt_images"]:
            print(
                f"- {image['file_name']}: "
                f"{image['error']}"
            )
    else:
        print("None detected.")

    print()
    print("IMAGE RECORDS")
    print("-" * 72)

    dataframe = pd.DataFrame(records)

    if not dataframe.empty:
        display_columns = [
            "file_name",
            "extension",
            "file_size_mb",
            "width",
            "height",
            "format",
            "aspect_ratio",
            "megapixels",
            "status",
        ]

        print(
            dataframe[display_columns]
            .to_string(index=False)
        )
    else:
        print("No records generated.")

    print()
    print("=" * 72)
    print("AUDIT COMPLETE")
    print("=" * 72)
    print()


def save_reports(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """
    Save CSV and JSON audit reports.
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    dataframe = pd.DataFrame(records)

    csv_path = REPORT_DIR / "dataset_audit.csv"
    json_path = REPORT_DIR / "dataset_audit.json"

    dataframe.to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    report = {
        "summary": summary,
        "records": records,
    }

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"CSV report : {csv_path}")
    print(f"JSON report: {json_path}")


def main() -> None:
    """
    Main program entry point.
    """
    print()
    print("Starting TowerVision dataset audit...")
    print(f"Scanning: {RAW_DIR}")
    print()

    all_files = find_files()

    image_files = [
        path
        for path in all_files
        if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    ]

    records = [
        build_image_record(file_path)
        for file_path in image_files
    ]

    summary = summarize(
        records=records,
        all_files=all_files,
    )

    save_reports(
        records=records,
        summary=summary,
    )

    print_console_report(
        summary=summary,
        records=records,
    )


if __name__ == "__main__":
    main()