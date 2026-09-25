from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# TowerVision AI
# Phase 1 - Repaired Annotation Validation
# ============================================================
#
# Purpose:
#   Validate the separately repaired annotation set.
#
# Images:
#   data/interim/annotation/images/
#
# Repaired labels:
#   data/interim/annotation_repaired/labels/
#
# Classes:
#   data/interim/annotation_repaired/classes.txt
#
# This script does NOT modify any images or annotations.
#
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation"
    / "images"
)

REPAIRED_ROOT = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation_repaired"
)

LABEL_DIR = (
    REPAIRED_ROOT
    / "labels"
)

CLASSES_PATH = (
    REPAIRED_ROOT
    / "classes.txt"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "reports"
)

OUTPUT_CSV = (
    REPORT_DIR
    / "repaired_annotation_validation.csv"
)

OUTPUT_JSON = (
    REPORT_DIR
    / "repaired_annotation_validation.json"
)

EXPECTED_CLASSES = [
    "supporting_tower",
    "monopole_tower",
]

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MIN_BOX_SIZE = 1e-9


def load_classes() -> list[str]:
    """
    Load and verify the class mapping.
    """
    if not CLASSES_PATH.exists():
        raise FileNotFoundError(
            f"Repaired classes.txt not found:\n{CLASSES_PATH}"
        )

    with CLASSES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        classes = [
            line.strip()
            for line in file
            if line.strip()
        ]

    if classes != EXPECTED_CLASSES:
        raise ValueError(
            "Class mapping mismatch.\n"
            f"Expected: {EXPECTED_CLASSES}\n"
            f"Found: {classes}"
        )

    return classes


def find_images() -> list[Path]:
    """
    Find annotation images.
    """
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(
            f"Image directory not found:\n{IMAGE_DIR}"
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


def find_labels() -> list[Path]:
    """
    Find repaired label files.
    """
    if not LABEL_DIR.exists():
        raise FileNotFoundError(
            f"Repaired label directory not found:\n{LABEL_DIR}"
        )

    return sorted(
        path
        for path in LABEL_DIR.glob("*.txt")
    )


def validate_values(
    parts: list[str],
    classes: list[str],
) -> list[str]:
    """
    Validate one YOLO annotation line.
    """
    errors: list[str] = []

    if len(parts) != 5:
        errors.append(
            f"expected_5_values_found_{len(parts)}"
        )
        return errors

    try:
        class_value = float(
            parts[0]
        )
    except ValueError:
        errors.append(
            "class_id_not_numeric"
        )
        return errors

    if not class_value.is_integer():
        errors.append(
            "class_id_not_integer"
        )
    else:
        class_id = int(
            class_value
        )

        if (
            class_id < 0
            or class_id >= len(classes)
        ):
            errors.append(
                "class_id_out_of_range"
            )

    coordinates: list[float] = []

    for index, value in enumerate(
        parts[1:],
        start=1,
    ):
        try:
            number = float(
                value
            )
        except ValueError:
            errors.append(
                f"coordinate_{index}_not_numeric"
            )
            continue

        if not (
            float("-inf")
            < number
            < float("inf")
        ):
            errors.append(
                f"coordinate_{index}_not_finite"
            )
            continue

        coordinates.append(
            number
        )

    if len(coordinates) != 4:
        return errors

    x_center, y_center, width, height = (
        coordinates
    )

    for name, value in [
        ("x_center", x_center),
        ("y_center", y_center),
        ("width", width),
        ("height", height),
    ]:
        if value < 0 or value > 1:
            errors.append(
                f"{name}_outside_0_1"
            )

    if width <= MIN_BOX_SIZE:
        errors.append(
            "width_zero_or_negative"
        )

    if height <= MIN_BOX_SIZE:
        errors.append(
            "height_zero_or_negative"
        )

    x1 = (
        x_center
        - width / 2
    )

    y1 = (
        y_center
        - height / 2
    )

    x2 = (
        x_center
        + width / 2
    )

    y2 = (
        y_center
        + height / 2
    )

    if x1 < 0:
        errors.append(
            "box_left_outside_image"
        )

    if y1 < 0:
        errors.append(
            "box_top_outside_image"
        )

    if x2 > 1:
        errors.append(
            "box_right_outside_image"
        )

    if y2 > 1:
        errors.append(
            "box_bottom_outside_image"
        )

    return errors


def validate_label(
    label_path: Path,
    classes: list[str],
) -> dict[str, Any]:
    """
    Validate one repaired label file.
    """
    errors: list[str] = []
    line_count = 0
    valid_box_count = 0

    class_counts = {
        "supporting_tower": 0,
        "monopole_tower": 0,
    }

    with label_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        lines = file.readlines()

    for line_number, raw_line in enumerate(
        lines,
        start=1,
    ):
        line = raw_line.strip()

        if not line:
            continue

        line_count += 1

        parts = line.split()

        line_errors = validate_values(
            parts=parts,
            classes=classes,
        )

        if line_errors:
            errors.extend(
                f"line_{line_number}:{error}"
                for error in line_errors
            )
            continue

        valid_box_count += 1

        class_id = int(
            float(parts[0])
        )

        class_counts[
            classes[class_id]
        ] += 1

    return {
        "line_count": line_count,
        "valid_box_count": valid_box_count,
        "error_count": len(errors),
        "errors": errors,
        "supporting_tower_count": (
            class_counts["supporting_tower"]
        ),
        "monopole_tower_count": (
            class_counts["monopole_tower"]
        ),
    }


def build_validation_records(
    images: list[Path],
    labels: list[Path],
    classes: list[str],
) -> list[dict[str, Any]]:
    """
    Validate every image/label pair.
    """
    image_map = {
        path.stem: path
        for path in images
    }

    label_map = {
        path.stem: path
        for path in labels
    }

    stems = sorted(
        set(image_map)
        | set(label_map)
    )

    records: list[dict[str, Any]] = []

    for index, stem in enumerate(
        stems,
        start=1,
    ):
        print(
            f"[{index:03d}/{len(stems):03d}] "
            f"{stem}"
        )

        image_path = image_map.get(
            stem
        )

        label_path = label_map.get(
            stem
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
            "line_count": 0,
            "valid_box_count": 0,
            "error_count": 0,
            "supporting_tower_count": 0,
            "monopole_tower_count": 0,
            "errors": "",
            "status": "valid",
        }

        if image_path is None:
            record["status"] = (
                "missing_image"
            )
            record["error_count"] = 1
            record["errors"] = (
                "missing_image"
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
                "missing_label"
            )

            records.append(
                record
            )
            continue

        result = validate_label(
            label_path=label_path,
            classes=classes,
        )

        record["line_count"] = (
            result["line_count"]
        )

        record["valid_box_count"] = (
            result["valid_box_count"]
        )

        record["error_count"] = (
            result["error_count"]
        )

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

        record["errors"] = (
            " | ".join(
                result["errors"]
            )
        )

        if result["errors"]:
            record["status"] = (
                "invalid"
            )

        records.append(
            record
        )

    return records


def build_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build aggregate validation statistics.
    """
    dataframe = pd.DataFrame(
        records
    )

    if dataframe.empty:
        return {
            "images": 0,
            "labels": 0,
            "invalid": 0,
            "boxes": 0,
        }

    invalid = int(
        (
            dataframe[
                "status"
            ]
            == "invalid"
        ).sum()
    )

    missing_labels = int(
        (
            ~dataframe[
                "label_exists"
            ]
        ).sum()
    )

    missing_images = int(
        (
            ~dataframe[
                "image_exists"
            ]
        ).sum()
    )

    return {
        "images": int(
            dataframe[
                "image_exists"
            ].sum()
        ),
        "labels": int(
            dataframe[
                "label_exists"
            ].sum()
        ),
        "invalid_images": invalid,
        "missing_labels": (
            missing_labels
        ),
        "missing_images": (
            missing_images
        ),
        "total_boxes": int(
            dataframe[
                "valid_box_count"
            ].sum()
        ),
        "supporting_tower": int(
            dataframe[
                "supporting_tower_count"
            ].sum()
        ),
        "monopole_tower": int(
            dataframe[
                "monopole_tower_count"
            ].sum()
        ),
        "validation_errors": int(
            dataframe[
                "error_count"
            ].sum()
        ),
    }


def save_reports(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """
    Save repaired annotation validation reports.
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
    Print validation results.
    """
    print()
    print("=" * 72)
    print(
        "REPAIRED ANNOTATION VALIDATION"
    )
    print("=" * 72)
    print()

    print(
        f"Images             : "
        f"{summary['images']}"
    )

    print(
        f"Labels             : "
        f"{summary['labels']}"
    )

    print(
        f"Missing labels     : "
        f"{summary['missing_labels']}"
    )

    print(
        f"Missing images     : "
        f"{summary['missing_images']}"
    )

    print(
        f"Invalid images     : "
        f"{summary['invalid_images']}"
    )

    print(
        f"Validation errors  : "
        f"{summary['validation_errors']}"
    )

    print(
        f"Valid boxes        : "
        f"{summary['total_boxes']}"
    )

    print()
    print(
        "CLASS DISTRIBUTION"
    )
    print("-" * 72)

    print(
        f"supporting_tower : "
        f"{summary['supporting_tower']}"
    )

    print(
        f"monopole_tower   : "
        f"{summary['monopole_tower']}"
    )

    print()
    print("=" * 72)

    if (
        summary["invalid_images"] == 0
        and summary["missing_labels"] == 0
        and summary["missing_images"] == 0
        and summary["validation_errors"] == 0
    ):
        print(
            "REPAIRED ANNOTATIONS: PASS"
        )
    else:
        print(
            "REPAIRED ANNOTATIONS: REVIEW REQUIRED"
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
        "TOWERVISION AI - REPAIRED ANNOTATION QA"
    )
    print("=" * 72)
    print()

    classes = load_classes()

    print(
        "Class mapping:"
    )

    for index, name in enumerate(
        classes
    ):
        print(
            f"  {index} = {name}"
        )

    print()

    images = find_images()
    labels = find_labels()

    print(
        f"Images found : {len(images)}"
    )

    print(
        f"Labels found : {len(labels)}"
    )

    print()
    print(
        "Validating repaired annotations..."
    )
    print()

    records = build_validation_records(
        images=images,
        labels=labels,
        classes=classes,
    )

    summary = build_summary(
        records
    )

    save_reports(
        records=records,
        summary=summary,
    )

    print_summary(
        summary
    )


if __name__ == "__main__":
    main()