from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# TowerVision AI
# Phase 1 - Boundary Annotation Repair
# ============================================================
#
# Purpose:
#   Repair ONLY tiny YOLO bounding-box boundary overflows.
#
# Example:
#
#   x_center = 0.500
#   y_center = 0.900
#   width    = 0.300
#   height   = 0.202
#
#   y2 = 0.900 + 0.101
#      = 1.001
#
# The box is intended to reach the image boundary.
# We move the center/size representation just enough so that
# the final box lies inside [0, 1].
#
# IMPORTANT:
#   - Original annotation files are NEVER overwritten.
#   - A backup copy of every source TXT file is created.
#   - Only boundary overflow <= MAX_ALLOWED_OVERFLOW is repaired.
#   - Larger problems are reported and left untouched.
#   - Image files are NEVER modified.
#
# Input:
#   data/interim/annotation/images/*.txt
#
# Output:
#   data/interim/annotation_repaired/labels/*.txt
#   data/interim/annotation_repaired/original_labels_backup/
#   data/reports/boundary_annotation_repair.csv
#   data/reports/boundary_annotation_repair.json
#
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation"
    / "images"
)

REPAIRED_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation_repaired"
)

REPAIRED_LABEL_DIR = (
    REPAIRED_DIR
    / "labels"
)

BACKUP_DIR = (
    REPAIRED_DIR
    / "original_labels_backup"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "reports"
)

REPORT_CSV = (
    REPORT_DIR
    / "boundary_annotation_repair.csv"
)

REPORT_JSON = (
    REPORT_DIR
    / "boundary_annotation_repair.json"
)

CLASSES_FILE_NAME = "classes.txt"

# Only tiny numerical boundary errors are automatically repaired.
#
# 0.001 normalized ~= 2 pixels when the image dimension is
# approximately 2048 pixels.
#
# Anything larger is considered suspicious and is NOT changed.
MAX_ALLOWED_OVERFLOW = 0.0015

FLOAT_PRECISION = 6


def find_label_files() -> list[Path]:
    """
    Find the actual image-associated annotation files.
    """
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"Annotation directory does not exist:\n{SOURCE_DIR}"
        )

    return sorted(
        path
        for path in SOURCE_DIR.glob("*.txt")
        if path.name.lower() != CLASSES_FILE_NAME
    )


def parse_line(
    line: str,
) -> tuple[int, float, float, float, float] | None:
    """
    Parse one YOLO annotation line.

    Returns:
        class_id, x_center, y_center, width, height

    Returns None for malformed lines.
    """
    parts = line.split()

    if len(parts) != 5:
        return None

    try:
        class_id_float = float(parts[0])

        if not class_id_float.is_integer():
            return None

        class_id = int(class_id_float)

        x_center = float(parts[1])
        y_center = float(parts[2])
        width = float(parts[3])
        height = float(parts[4])

    except ValueError:
        return None

    return (
        class_id,
        x_center,
        y_center,
        width,
        height,
    )


def calculate_corners(
    x_center: float,
    y_center: float,
    width: float,
    height: float,
) -> tuple[float, float, float, float]:
    """
    Convert YOLO center/width/height representation to corners.
    """
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

    return (
        x1,
        y1,
        x2,
        y2,
    )


def repair_box(
    class_id: int,
    x_center: float,
    y_center: float,
    width: float,
    height: float,
) -> tuple[str, dict[str, Any]]:
    """
    Repair a YOLO box if and only if the overflow is tiny.

    The repair is performed in corner space:

        x1, y1, x2, y2

    Any tiny coordinate outside [0,1] is clipped to the boundary.

    The resulting corners are converted back into YOLO format.

    Returns:
        repaired_line
        metadata
    """
    x1, y1, x2, y2 = calculate_corners(
        x_center,
        y_center,
        width,
        height,
    )

    left_overflow = max(
        0.0,
        -x1,
    )

    top_overflow = max(
        0.0,
        -y1,
    )

    right_overflow = max(
        0.0,
        x2 - 1.0,
    )

    bottom_overflow = max(
        0.0,
        y2 - 1.0,
    )

    max_overflow = max(
        left_overflow,
        top_overflow,
        right_overflow,
        bottom_overflow,
    )

    has_overflow = (
        max_overflow > 0
    )

    repair_allowed = (
        has_overflow
        and max_overflow
        <= MAX_ALLOWED_OVERFLOW
    )

    # No boundary problem.
    if not has_overflow:
        metadata = {
            "status": "unchanged",
            "reason": "inside_boundary",
            "max_overflow": 0.0,
            "changed": False,
        }

        return (
            f"{class_id} "
            f"{x_center:.{FLOAT_PRECISION}f} "
            f"{y_center:.{FLOAT_PRECISION}f} "
            f"{width:.{FLOAT_PRECISION}f} "
            f"{height:.{FLOAT_PRECISION}f}",
            metadata,
        )

    # Boundary problem exists, but is too large for automatic
    # repair.
    if not repair_allowed:
        metadata = {
            "status": "manual_review",
            "reason": "overflow_too_large",
            "max_overflow": max_overflow,
            "changed": False,
        }

        return (
            f"{class_id} "
            f"{x_center:.{FLOAT_PRECISION}f} "
            f"{y_center:.{FLOAT_PRECISION}f} "
            f"{width:.{FLOAT_PRECISION}f} "
            f"{height:.{FLOAT_PRECISION}f}",
            metadata,
        )

    # --------------------------------------------------------
    # Controlled boundary clipping.
    # --------------------------------------------------------

    repaired_x1 = max(
        0.0,
        min(1.0, x1),
    )

    repaired_y1 = max(
        0.0,
        min(1.0, y1),
    )

    repaired_x2 = max(
        0.0,
        min(1.0, x2),
    )

    repaired_y2 = max(
        0.0,
        min(1.0, y2),
    )

    repaired_width = (
        repaired_x2
        - repaired_x1
    )

    repaired_height = (
        repaired_y2
        - repaired_y1
    )

    repaired_x_center = (
        repaired_x1
        + repaired_x2
    ) / 2.0

    repaired_y_center = (
        repaired_y1
        + repaired_y2
    ) / 2.0

    repaired_line = (
        f"{class_id} "
        f"{repaired_x_center:.{FLOAT_PRECISION}f} "
        f"{repaired_y_center:.{FLOAT_PRECISION}f} "
        f"{repaired_width:.{FLOAT_PRECISION}f} "
        f"{repaired_height:.{FLOAT_PRECISION}f}"
    )

    if (
        bottom_overflow > 0
        and right_overflow > 0
    ):
        reason = "bottom_and_right_clipped"

    elif bottom_overflow > 0:
        reason = "bottom_clipped"

    elif right_overflow > 0:
        reason = "right_clipped"

    elif top_overflow > 0:
        reason = "top_clipped"

    elif left_overflow > 0:
        reason = "left_clipped"

    else:
        reason = "boundary_clipped"

    metadata = {
        "status": "repaired",
        "reason": reason,
        "max_overflow": max_overflow,
        "changed": True,
        "original_corners": [
            x1,
            y1,
            x2,
            y2,
        ],
        "repaired_corners": [
            repaired_x1,
            repaired_y1,
            repaired_x2,
            repaired_y2,
        ],
    }

    return (
        repaired_line,
        metadata,
    )


def process_label_file(
    label_path: Path,
) -> tuple[dict[str, Any], str]:
    """
    Repair one complete label file.
    """
    with label_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        lines = file.readlines()

    output_lines: list[str] = []

    file_changed = False
    repaired_boxes = 0
    manual_review_boxes = 0
    unchanged_boxes = 0
    malformed_lines = 0

    max_overflow = 0.0

    line_details: list[dict[str, Any]] = []

    for line_number, raw_line in enumerate(
        lines,
        start=1,
    ):
        stripped = raw_line.strip()

        if not stripped:
            continue

        parsed = parse_line(
            stripped
        )

        if parsed is None:
            malformed_lines += 1

            output_lines.append(
                stripped
            )

            line_details.append(
                {
                    "line_number": line_number,
                    "status": "malformed",
                    "changed": False,
                }
            )

            continue

        (
            class_id,
            x_center,
            y_center,
            width,
            height,
        ) = parsed

        repaired_line, metadata = repair_box(
            class_id=class_id,
            x_center=x_center,
            y_center=y_center,
            width=width,
            height=height,
        )

        output_lines.append(
            repaired_line
        )

        status = metadata[
            "status"
        ]

        if status == "repaired":
            repaired_boxes += 1
            file_changed = True

        elif status == "manual_review":
            manual_review_boxes += 1

        else:
            unchanged_boxes += 1

        max_overflow = max(
            max_overflow,
            float(
                metadata[
                    "max_overflow"
                ]
            ),
        )

        detail = {
            "line_number": line_number,
            "class_id": class_id,
            "status": status,
            "reason": metadata[
                "reason"
            ],
            "max_overflow": metadata[
                "max_overflow"
            ],
            "changed": metadata[
                "changed"
            ],
        }

        line_details.append(
            detail
        )

    result = {
        "label_file": label_path.name,
        "changed": file_changed,
        "total_lines": len(
            output_lines
        ),
        "repaired_boxes": repaired_boxes,
        "manual_review_boxes": (
            manual_review_boxes
        ),
        "unchanged_boxes": unchanged_boxes,
        "malformed_lines": malformed_lines,
        "max_overflow": max_overflow,
        "line_details": line_details,
    }

    output_text = "\n".join(
        output_lines
    )

    if output_lines:
        output_text += "\n"

    return (
        result,
        output_text,
    )


def prepare_directories() -> None:
    """
    Create output directories.
    """
    REPAIRED_LABEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def backup_original_label(
    label_path: Path,
) -> None:
    """
    Copy an original annotation to a dedicated backup directory.
    """
    destination = (
        BACKUP_DIR
        / label_path.name
    )

    shutil.copy2(
        label_path,
        destination,
    )


def copy_classes_file() -> None:
    """
    Copy classes.txt into the repaired annotation directory.
    """
    source = (
        SOURCE_DIR
        / CLASSES_FILE_NAME
    )

    if source.exists():
        destination = (
            REPAIRED_DIR
            / CLASSES_FILE_NAME
        )

        shutil.copy2(
            source,
            destination,
        )


def build_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build repair summary statistics.
    """
    total_files = len(
        records
    )

    changed_files = sum(
        1
        for record in records
        if record["changed"]
    )

    repaired_boxes = sum(
        record["repaired_boxes"]
        for record in records
    )

    manual_review_boxes = sum(
        record["manual_review_boxes"]
        for record in records
    )

    malformed_lines = sum(
        record["malformed_lines"]
        for record in records
    )

    return {
        "annotation_files": total_files,
        "changed_files": changed_files,
        "unchanged_files": (
            total_files
            - changed_files
        ),
        "repaired_boxes": repaired_boxes,
        "manual_review_boxes": (
            manual_review_boxes
        ),
        "malformed_lines": malformed_lines,
        "maximum_observed_overflow": max(
            (
                record["max_overflow"]
                for record in records
            ),
            default=0.0,
        ),
        "automatic_repair_limit": (
            MAX_ALLOWED_OVERFLOW
        ),
    }


def save_reports(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """
    Save repair report files.
    """
    dataframe = pd.DataFrame(
        [
            {
                key: value
                for key, value in record.items()
                if key != "line_details"
            }
            for record in records
        ]
    )

    dataframe.to_csv(
        REPORT_CSV,
        index=False,
        encoding="utf-8",
    )

    payload = {
        "summary": summary,
        "records": records,
    }

    with REPORT_JSON.open(
        "w",
        encoding="utf-8",
    ) as file:
        import json

        json.dump(
            payload,
            file,
            indent=2,
        )


def print_summary(
    summary: dict[str, Any],
) -> None:
    """
    Print the repair summary.
    """
    print()
    print("=" * 72)
    print(
        "BOUNDARY ANNOTATION REPAIR"
    )
    print("=" * 72)
    print()

    print(
        f"Annotation files       : "
        f"{summary['annotation_files']}"
    )

    print(
        f"Changed files         : "
        f"{summary['changed_files']}"
    )

    print(
        f"Unchanged files       : "
        f"{summary['unchanged_files']}"
    )

    print(
        f"Repaired boxes        : "
        f"{summary['repaired_boxes']}"
    )

    print(
        f"Manual review boxes   : "
        f"{summary['manual_review_boxes']}"
    )

    print(
        f"Malformed lines       : "
        f"{summary['malformed_lines']}"
    )

    print(
        f"Maximum overflow     : "
        f"{summary['maximum_observed_overflow']:.6f}"
    )

    print(
        f"Automatic repair max : "
        f"{summary['automatic_repair_limit']:.6f}"
    )

    print()
    print(
        "Original annotations were NOT overwritten."
    )

    print(
        "Repaired annotations were written separately."
    )

    print()


def main() -> None:
    """
    Main program entry point.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - CONTROLLED "
        "BOUNDARY ANNOTATION REPAIR"
    )
    print("=" * 72)
    print()

    prepare_directories()

    copy_classes_file()

    label_files = find_label_files()

    print(
        f"Label files found: "
        f"{len(label_files)}"
    )

    records: list[dict[str, Any]] = []

    for index, label_path in enumerate(
        label_files,
        start=1,
    ):
        print(
            f"[{index:03d}/{len(label_files):03d}] "
            f"{label_path.name}"
        )

        backup_original_label(
            label_path
        )

        result, output_text = (
            process_label_file(
                label_path
            )
        )

        records.append(
            result
        )

        destination = (
            REPAIRED_LABEL_DIR
            / label_path.name
        )

        with destination.open(
            "w",
            encoding="utf-8",
        ) as file:
            file.write(
                output_text
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

    print(
        f"Repaired labels: "
        f"{REPAIRED_LABEL_DIR}"
    )

    print(
        f"Original backup: "
        f"{BACKUP_DIR}"
    )

    print(
        f"Report CSV: "
        f"{REPORT_CSV}"
    )

    print(
        f"Report JSON: "
        f"{REPORT_JSON}"
    )


if __name__ == "__main__":
    main()