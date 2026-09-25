from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# TowerVision AI
# Phase 1 - Annotation Validation
# ============================================================
#
# Purpose:
#   Automatically validate the YOLO annotations created by the
#   annotation process.
#
# Input:
#   data/interim/annotation/images/
#   data/interim/annotation/classes.txt
#   data/interim/annotation/annotation_manifest.csv
#
# Expected classes:
#   0 = supporting_tower
#   1 = monopole_tower
#
# Validation:
#   - Every image has a corresponding label file
#   - Every label belongs to a known class
#   - Every line has exactly 5 values
#   - Class ID is valid
#   - Bounding box values are numeric
#   - Coordinates are normalized to [0, 1]
#   - Width and height are > 0
#   - Bounding box stays within normalized image space
#   - Empty label files are allowed as explicit negative images
#   - Annotation/image counts are reported
#
# IMPORTANT:
#   This script does NOT modify any images or labels.
#
# Outputs:
#   data/reports/annotation_validation.csv
#   data/reports/annotation_validation.json
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ANNOTATION_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation"
)

IMAGE_DIR = (
    ANNOTATION_DIR
    / "images"
)

CLASSES_PATH = (
    ANNOTATION_DIR
    / "classes.txt"
)

MANIFEST_PATH = (
    ANNOTATION_DIR
    / "annotation_manifest.csv"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "reports"
)

OUTPUT_CSV = (
    REPORT_DIR
    / "annotation_validation.csv"
)

OUTPUT_JSON = (
    REPORT_DIR
    / "annotation_validation.json"
)

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


EXPECTED_CLASS_COUNT = 2

MIN_BOX_SIZE = 1e-6

# A box occupying more than this fraction of the image can be
# legitimate for a large tower. It is only flagged as
# "suspicious" for manual review; it is NOT automatically invalid.
MAX_SUSPICIOUS_BOX_AREA = 0.98


def load_classes() -> list[str]:
    """
    Load class names from classes.txt.
    """
    if not CLASSES_PATH.exists():
        raise FileNotFoundError(
            f"classes.txt not found:\n{CLASSES_PATH}"
        )

    classes = []

    with CLASSES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            name = line.strip()

            if name:
                classes.append(name)

    if len(classes) != EXPECTED_CLASS_COUNT:
        raise ValueError(
            "Unexpected number of classes.\n"
            f"Expected: {EXPECTED_CLASS_COUNT}\n"
            f"Found: {len(classes)}\n"
            f"Classes: {classes}"
        )

    expected = [
        "supporting_tower",
        "monopole_tower",
    ]

    if classes != expected:
        raise ValueError(
            "Class order does not match the required mapping.\n"
            f"Expected: {expected}\n"
            f"Found: {classes}"
        )

    return classes


def find_images() -> list[Path]:
    """
    Find all actual image files in the annotation directory.
    """
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(
            f"Annotation image directory not found:\n{IMAGE_DIR}"
        )

    return sorted(
        path
        for path in IMAGE_DIR.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_IMAGE_EXTENSIONS
        )
    )


def find_label_files() -> list[Path]:
    """
    Find all label TXT files, excluding classes.txt.
    """
    return sorted(
        path
        for path in IMAGE_DIR.iterdir()
        if (
            path.is_file()
            and path.suffix.lower() == ".txt"
        )
    )


def read_label_lines(
    label_path: Path,
) -> list[str]:
    """
    Read non-empty label lines.

    An empty annotation file is allowed and means the image has
    no annotated target object.
    """
    with label_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return [
            line.strip()
            for line in file
            if line.strip()
        ]


def validate_box_values(
    values: list[str],
    class_names: list[str],
) -> list[str]:
    """
    Validate one YOLO annotation line.

    Format:
        class_id x_center y_center width height

    Returns a list of validation errors/warnings.
    """
    problems: list[str] = []

    if len(values) != 5:
        problems.append(
            f"expected_5_values_found_{len(values)}"
        )

        return problems

    try:
        class_id_float = float(
            values[0]
        )
    except ValueError:
        problems.append(
            "class_id_not_numeric"
        )
        class_id_float = None

    if class_id_float is not None:
        if not class_id_float.is_integer():
            problems.append(
                "class_id_not_integer"
            )
        else:
            class_id = int(
                class_id_float
            )

            if (
                class_id < 0
                or class_id >= len(class_names)
            ):
                problems.append(
                    "class_id_out_of_range"
                )

    numeric_values: list[float] = []

    for value in values[1:]:
        try:
            number = float(value)

            if number != number:
                problems.append(
                    "nan_coordinate"
                )
                continue

            if number in (
                float("inf"),
                float("-inf"),
            ):
                problems.append(
                    "infinite_coordinate"
                )
                continue

            numeric_values.append(
                number
            )

        except ValueError:
            problems.append(
                "coordinate_not_numeric"
            )

    if len(numeric_values) != 4:
        return problems

    x_center, y_center, width, height = (
        numeric_values
    )

    # YOLO normalized coordinates must be in [0, 1].
    for name, value in [
        ("x_center", x_center),
        ("y_center", y_center),
        ("width", width),
        ("height", height),
    ]:
        if value < 0 or value > 1:
            problems.append(
                f"{name}_outside_0_1"
            )

    if width <= MIN_BOX_SIZE:
        problems.append(
            "box_width_zero_or_negative"
        )

    if height <= MIN_BOX_SIZE:
        problems.append(
            "box_height_zero_or_negative"
        )

    # Calculate box corners.
    x1 = x_center - (
        width / 2
    )

    y1 = y_center - (
        height / 2
    )

    x2 = x_center + (
        width / 2
    )

    y2 = y_center + (
        height / 2
    )

    if x1 < 0:
        problems.append(
            "box_left_outside_image"
        )

    if y1 < 0:
        problems.append(
            "box_top_outside_image"
        )

    if x2 > 1:
        problems.append(
            "box_right_outside_image"
        )

    if y2 > 1:
        problems.append(
            "box_bottom_outside_image"
        )

    # Large-area boxes aren't automatically wrong.
    # They are only marked as suspicious later.
    return problems


def calculate_box_area(
    values: list[str],
) -> float | None:
    """
    Calculate normalized bounding-box area.
    """
    if len(values) != 5:
        return None

    try:
        width = float(
            values[3]
        )

        height = float(
            values[4]
        )

    except ValueError:
        return None

    if width <= 0 or height <= 0:
        return None

    return width * height


def validate_label_file(
    label_path: Path,
    class_names: list[str],
) -> dict[str, Any]:
    """
    Validate every annotation line in one label file.
    """
    lines = read_label_lines(
        label_path
    )

    errors: list[str] = []
    warnings: list[str] = []

    valid_boxes = 0

    class_counts = {
        class_name: 0
        for class_name in class_names
    }

    suspicious_large_boxes = 0

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        values = line.split()

        problems = validate_box_values(
            values=values,
            class_names=class_names,
        )

        if problems:
            for problem in problems:
                errors.append(
                    f"line_{line_number}:{problem}"
                )

        if len(values) == 5:
            try:
                class_id = int(
                    float(values[0])
                )

                if (
                    0 <= class_id
                    < len(class_names)
                    and float(values[0]).is_integer()
                ):
                    class_counts[
                        class_names[class_id]
                    ] += 1

            except ValueError:
                pass

            area = calculate_box_area(
                values
            )

            if (
                area is not None
                and area
                >= MAX_SUSPICIOUS_BOX_AREA
            ):
                suspicious_large_boxes += 1

        if not problems:
            valid_boxes += 1

    if suspicious_large_boxes > 0:
        warnings.append(
            "contains_very_large_box"
        )

    is_empty_label = (
        len(lines) == 0
    )

    if is_empty_label:
        warnings.append(
            "empty_annotation_file"
        )

    return {
        "label_file": label_path.name,
        "line_count": len(lines),
        "valid_box_count": valid_boxes,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "is_empty_label": is_empty_label,
        "suspicious_large_boxes": (
            suspicious_large_boxes
        ),
        "supporting_tower_count": class_counts[
            "supporting_tower"
        ],
        "monopole_tower_count": class_counts[
            "monopole_tower"
        ],
        "errors": errors,
        "warnings": warnings,
    }


def map_images_to_labels(
    images: list[Path],
    label_files: list[Path],
) -> tuple[
    dict[str, Path],
    dict[str, Path],
]:
    """
    Create image and label lookup maps based on filename stem.
    """
    image_map = {
        path.stem: path
        for path in images
    }

    label_map = {
        path.stem: path
        for path in label_files
        if path.name.lower()
        != "classes.txt"
    }

    return (
        image_map,
        label_map,
    )


def build_records(
    images: list[Path],
    label_files: list[Path],
    class_names: list[str],
) -> list[dict[str, Any]]:
    """
    Validate every image-label pair.
    """
    image_map, label_map = map_images_to_labels(
        images,
        label_files,
    )

    all_stems = sorted(
        set(image_map)
        | set(label_map)
    )

    records: list[dict[str, Any]] = []

    for index, stem in enumerate(
        all_stems,
        start=1,
    ):
        image_path = image_map.get(
            stem
        )

        label_path = label_map.get(
            stem
        )

        print(
            f"[{index:03d}/{len(all_stems):03d}] "
            f"{stem}"
        )

        record: dict[str, Any] = {
            "file_stem": stem,
            "image_file": (
                image_path.name
                if image_path
                else ""
            ),
            "label_file": (
                label_path.name
                if label_path
                else ""
            ),
            "image_exists": (
                image_path is not None
            ),
            "label_exists": (
                label_path is not None
            ),
            "label_line_count": 0,
            "valid_box_count": 0,
            "error_count": 0,
            "warning_count": 0,
            "is_empty_label": False,
            "suspicious_large_boxes": 0,
            "supporting_tower_count": 0,
            "monopole_tower_count": 0,
            "status": "valid",
            "errors": "",
            "warnings": "",
        }

        if image_path is None:
            record["status"] = (
                "missing_image"
            )

            record["error_count"] = 1

            record["errors"] = (
                "image_missing_for_label"
            )

            records.append(
                record
            )

            continue

        if label_path is None:
            record["status"] = (
                "missing_label"
            )

            record["error_count"] = 1

            record["errors"] = (
                "annotation_file_missing"
            )

            records.append(
                record
            )

            continue

        result = validate_label_file(
            label_path=label_path,
            class_names=class_names,
        )

        record[
            "label_line_count"
        ] = result[
            "line_count"
        ]

        record[
            "valid_box_count"
        ] = result[
            "valid_box_count"
        ]

        record[
            "error_count"
        ] = result[
            "error_count"
        ]

        record[
            "warning_count"
        ] = result[
            "warning_count"
        ]

        record[
            "is_empty_label"
        ] = result[
            "is_empty_label"
        ]

        record[
            "suspicious_large_boxes"
        ] = result[
            "suspicious_large_boxes"
        ]

        record[
            "supporting_tower_count"
        ] = result[
            "supporting_tower_count"
        ]

        record[
            "monopole_tower_count"
        ] = result[
            "monopole_tower_count"
        ]

        errors = result[
            "errors"
        ]

        warnings = result[
            "warnings"
        ]

        record["errors"] = (
            " | ".join(errors)
        )

        record["warnings"] = (
            " | ".join(warnings)
        )

        if errors:
            record["status"] = (
                "invalid"
            )

        elif warnings:
            record["status"] = (
                "valid_with_warnings"
            )

        records.append(
            record
        )

    return records


def build_summary(
    records: list[dict[str, Any]],
    class_names: list[str],
) -> dict[str, Any]:
    """
    Build the final validation summary.
    """
    dataframe = pd.DataFrame(
        records
    )

    total_images = len(
        records
    )

    if total_images == 0:
        return {
            "images": 0,
            "labels": 0,
            "valid": 0,
            "invalid": 0,
        }

    missing_labels = int(
        (
            ~dataframe[
                "label_exists"
            ]
        )
        .sum()
    )

    missing_images = int(
        (
            ~dataframe[
                "image_exists"
            ]
        )
        .sum()
    )

    invalid = int(
        (
            dataframe[
                "status"
            ]
            == "invalid"
        )
        .sum()
    )

    valid_with_warnings = int(
        (
            dataframe[
                "status"
            ]
            == "valid_with_warnings"
        )
        .sum()
    )

    fully_valid = int(
        (
            dataframe[
                "status"
            ]
            == "valid"
        )
        .sum()
    )

    empty_labels = int(
        dataframe[
            "is_empty_label"
        ].sum()
    )

    invalid_boxes = int(
        dataframe[
            "error_count"
        ].sum()
    )

    suspicious_large_boxes = int(
        dataframe[
            "suspicious_large_boxes"
        ].sum()
    )

    total_boxes = int(
        dataframe[
            "valid_box_count"
        ].sum()
    )

    class_distribution = {}

    for class_name in class_names:
        column = (
            f"{class_name}_count"
        )

        class_distribution[
            class_name
        ] = int(
            dataframe[column].sum()
        )

    return {
        "image_files": total_images,
        "label_files": int(
            dataframe[
                "label_exists"
            ].sum()
        ),
        "missing_labels": missing_labels,
        "missing_images": missing_images,
        "fully_valid_images": fully_valid,
        "valid_with_warnings": (
            valid_with_warnings
        ),
        "invalid_images": invalid,
        "empty_annotation_files": (
            empty_labels
        ),
        "total_valid_boxes": total_boxes,
        "total_validation_errors": (
            invalid_boxes
        ),
        "suspicious_large_boxes": (
            suspicious_large_boxes
        ),
        "class_distribution": (
            class_distribution
        ),
    }


def save_reports(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    class_names: list[str],
) -> None:
    """
    Save CSV and JSON reports.
    """
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = pd.DataFrame(
        records
    )

    dataframe.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8",
    )

    payload = {
        "classes": {
            str(index): name
            for index, name
            in enumerate(class_names)
        },
        "summary": summary,
        "records": records,
    }

    with OUTPUT_JSON.open(
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
        f"CSV report : {OUTPUT_CSV}"
    )

    print(
        f"JSON report: {OUTPUT_JSON}"
    )


def print_summary(
    summary: dict[str, Any],
) -> None:
    """
    Print the validation summary.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - ANNOTATION VALIDATION"
    )
    print("=" * 72)

    print()
    print(
        f"Images                   : "
        f"{summary['image_files']}"
    )

    print(
        f"Label files              : "
        f"{summary['label_files']}"
    )

    print(
        f"Missing labels           : "
        f"{summary['missing_labels']}"
    )

    print(
        f"Missing images           : "
        f"{summary['missing_images']}"
    )

    print(
        f"Fully valid images       : "
        f"{summary['fully_valid_images']}"
    )

    print(
        f"Valid with warnings      : "
        f"{summary['valid_with_warnings']}"
    )

    print(
        f"Invalid images           : "
        f"{summary['invalid_images']}"
    )

    print(
        f"Empty annotation files   : "
        f"{summary['empty_annotation_files']}"
    )

    print(
        f"Valid bounding boxes     : "
        f"{summary['total_valid_boxes']}"
    )

    print(
        f"Validation errors        : "
        f"{summary['total_validation_errors']}"
    )

    print(
        f"Large-box warnings       : "
        f"{summary['suspicious_large_boxes']}"
    )

    print()
    print(
        "CLASS DISTRIBUTION"
    )
    print("-" * 72)

    for (
        class_name,
        count,
    ) in summary[
        "class_distribution"
    ].items():
        print(
            f"{class_name:25} "
            f"{count}"
        )

    print()
    print("=" * 72)

    if summary["invalid_images"] == 0:
        print(
            "ANNOTATION STRUCTURE: PASS"
        )
    else:
        print(
            "ANNOTATION STRUCTURE: REVIEW REQUIRED"
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
        "TOWERVISION AI - PHASE 1 ANNOTATION QA"
    )
    print("=" * 72)
    print()

    class_names = load_classes()

    print(
        "Class mapping:"
    )

    for index, class_name in enumerate(
        class_names
    ):
        print(
            f"  {index} = {class_name}"
        )

    images = find_images()

    label_files = find_label_files()

    print()
    print(
        f"Images found : {len(images)}"
    )

    print(
        f"TXT files    : {len(label_files)}"
    )

    print()
    print(
        "Validating annotations..."
    )
    print()

    records = build_records(
        images=images,
        label_files=label_files,
        class_names=class_names,
    )

    summary = build_summary(
        records=records,
        class_names=class_names,
    )

    save_reports(
        records=records,
        summary=summary,
        class_names=class_names,
    )

    print_summary(
        summary
    )

    # Don't terminate the process with a non-zero exit code.
    # We want the complete report even when issues exist.
    #
    # The summary determines whether the dataset can move on.
    if summary["invalid_images"] > 0:
        print(
            "Fix the reported annotation errors "
            "before continuing to dataset splitting."
        )


if __name__ == "__main__":
    main()