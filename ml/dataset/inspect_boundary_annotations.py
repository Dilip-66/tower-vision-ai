from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# TowerVision AI
# Phase 1 - Boundary Annotation Inspection
# ============================================================
#
# Purpose:
#   Diagnose annotations whose bounding boxes extend beyond
#   normalized image boundaries.
#
# IMPORTANT:
#   Annotation TXT files are stored beside the images:
#
#       data/interim/annotation/images/*.txt
#
#   This script only READS the data.
#   It never modifies annotations or images.
#
# Outputs:
#   data/reports/boundary_annotation_review.csv
#   data/interim/boundary_annotation_review.jpg
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ANNOTATION_ROOT = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation"
)

IMAGE_DIR = (
    ANNOTATION_ROOT
    / "images"
)

CLASSES_PATH = (
    ANNOTATION_ROOT
    / "classes.txt"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "reports"
)

OUTPUT_CSV = (
    REPORT_DIR
    / "boundary_annotation_review.csv"
)

OUTPUT_IMAGE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "boundary_annotation_review.jpg"
)

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MAX_IMAGES_ON_SHEET = 54
COLUMNS = 3

THUMBNAIL_WIDTH = 420
THUMBNAIL_HEIGHT = 300
LABEL_HEIGHT = 92

BACKGROUND = (245, 245, 245)
BOX_COLOR = (220, 40, 40)
TEXT_COLOR = (20, 20, 20)
BORDER_COLOR = (150, 150, 150)


def load_classes() -> list[str]:
    """
    Load class names from classes.txt.
    """
    if not CLASSES_PATH.exists():
        raise FileNotFoundError(
            f"classes.txt not found:\n{CLASSES_PATH}"
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

    if not classes:
        raise ValueError(
            "classes.txt is empty."
        )

    return classes


def find_annotation_files() -> list[Path]:
    """
    Find annotation files in the SAME directory as the images.
    """
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(
            f"Annotation image directory not found:\n{IMAGE_DIR}"
        )

    return sorted(
        path
        for path in IMAGE_DIR.glob("*.txt")
    )


def find_image_for_label(
    label_path: Path,
) -> Path | None:
    """
    Find the image matching a label file stem.
    """
    for extension in (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    ):
        image_path = (
            IMAGE_DIR
            / f"{label_path.stem}{extension}"
        )

        if image_path.exists():
            return image_path

    return None


def parse_label_line(
    line: str,
    line_number: int,
    classes: list[str],
) -> dict[str, Any] | None:
    """
    Parse one YOLO annotation line.
    """
    parts = line.split()

    if len(parts) != 5:
        return None

    try:
        class_id_float = float(parts[0])

        if not class_id_float.is_integer():
            return None

        class_id = int(
            class_id_float
        )

        x_center = float(parts[1])
        y_center = float(parts[2])
        width = float(parts[3])
        height = float(parts[4])

    except ValueError:
        return None

    if (
        class_id < 0
        or class_id >= len(classes)
    ):
        class_name = "unknown"
    else:
        class_name = classes[class_id]

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

    return {
        "line_number": line_number,
        "class_id": class_id,
        "class_name": class_name,
        "x_center": x_center,
        "y_center": y_center,
        "width_norm": width,
        "height_norm": height,
        "x1_norm": x1,
        "y1_norm": y1,
        "x2_norm": x2,
        "y2_norm": y2,
        "left_overflow": max(
            0.0,
            -x1,
        ),
        "top_overflow": max(
            0.0,
            -y1,
        ),
        "right_overflow": max(
            0.0,
            x2 - 1.0,
        ),
        "bottom_overflow": max(
            0.0,
            y2 - 1.0,
        ),
    }


def inspect_label_file(
    label_path: Path,
    classes: list[str],
) -> list[dict[str, Any]]:
    """
    Inspect every annotation box in one TXT file.
    """
    image_path = find_image_for_label(
        label_path
    )

    if image_path is None:
        return []

    with Image.open(
        image_path
    ) as image:
        image_width = image.width
        image_height = image.height

    rows: list[dict[str, Any]] = []

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

        parsed = parse_label_line(
            line=line,
            line_number=line_number,
            classes=classes,
        )

        if parsed is None:
            continue

        boundary_problems: list[str] = []

        if parsed["left_overflow"] > 0:
            boundary_problems.append("left")

        if parsed["top_overflow"] > 0:
            boundary_problems.append("top")

        if parsed["right_overflow"] > 0:
            boundary_problems.append("right")

        if parsed["bottom_overflow"] > 0:
            boundary_problems.append("bottom")

        if not boundary_problems:
            continue

        parsed.update(
            {
                "file_stem": label_path.stem,
                "image_file": image_path.name,
                "label_file": label_path.name,
                "image_width": image_width,
                "image_height": image_height,
                "boundary_problem": ",".join(
                    boundary_problems
                ),
                "raw_label": line,
            }
        )

        parsed[
            "max_overflow_norm"
        ] = max(
            parsed["left_overflow"],
            parsed["top_overflow"],
            parsed["right_overflow"],
            parsed["bottom_overflow"],
        )

        parsed[
            "max_overflow_pixels"
        ] = (
            parsed["max_overflow_norm"]
            * max(
                image_width,
                image_height,
            )
        )

        rows.append(
            parsed
        )

    return rows


def build_report(
    classes: list[str],
) -> pd.DataFrame:
    """
    Build the complete boundary-violation report.
    """
    label_files = find_annotation_files()

    print(
        f"Annotation files found: "
        f"{len(label_files)}"
    )

    rows: list[dict[str, Any]] = []

    total = len(label_files)

    for index, label_path in enumerate(
        label_files,
        start=1,
    ):
        print(
            f"[{index:03d}/{total:03d}] "
            f"{label_path.name}"
        )

        rows.extend(
            inspect_label_file(
                label_path=label_path,
                classes=classes,
            )
        )

    return pd.DataFrame(
        rows
    )


def load_image(
    row: pd.Series,
) -> Image.Image:
    """
    Load the affected image.
    """
    image_path = (
        IMAGE_DIR
        / str(row["image_file"])
    )

    return Image.open(
        image_path
    ).convert("RGB")


def create_contact_sheet(
    dataframe: pd.DataFrame,
) -> None:
    """
    Create a visual sheet showing all detected boundary
    violations.
    """
    if dataframe.empty:
        print()
        print(
            "No boundary violations found."
        )
        return

    dataframe = (
        dataframe
        .sort_values(
            "max_overflow_pixels",
            ascending=False,
        )
        .head(
            MAX_IMAGES_ON_SHEET
        )
        .reset_index(drop=True)
    )

    rows_count = math.ceil(
        len(dataframe)
        / COLUMNS
    )

    cell_width = (
        THUMBNAIL_WIDTH
    )

    cell_height = (
        THUMBNAIL_HEIGHT
        + LABEL_HEIGHT
    )

    sheet = Image.new(
        "RGB",
        (
            cell_width * COLUMNS,
            cell_height * rows_count,
        ),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(
        sheet
    )

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for index, (_, row) in enumerate(
        dataframe.iterrows()
    ):
        column = (
            index
            % COLUMNS
        )

        row_number = (
            index
            // COLUMNS
        )

        origin_x = (
            column
            * cell_width
        )

        origin_y = (
            row_number
            * cell_height
        )

        try:
            image = load_image(
                row
            )

            original_width = image.width
            original_height = image.height

            scale = min(
                (
                    THUMBNAIL_WIDTH
                    - 12
                )
                / original_width,
                (
                    THUMBNAIL_HEIGHT
                    - 12
                )
                / original_height,
            )

            display_width = max(
                1,
                int(
                    original_width
                    * scale
                ),
            )

            display_height = max(
                1,
                int(
                    original_height
                    * scale
                ),
            )

            image = image.resize(
                (
                    display_width,
                    display_height,
                ),
                Image.Resampling.LANCZOS,
            )

            paste_x = (
                origin_x
                + (
                    cell_width
                    - display_width
                )
                // 2
            )

            paste_y = (
                origin_y
                + (
                    THUMBNAIL_HEIGHT
                    - display_height
                )
                // 2
            )

            sheet.paste(
                image,
                (
                    paste_x,
                    paste_y,
                ),
            )

            local_draw = ImageDraw.Draw(
                sheet
            )

            local_draw.rectangle(
                [
                    paste_x,
                    paste_y,
                    paste_x
                    + display_width,
                    paste_y
                    + display_height,
                ],
                outline=BORDER_COLOR,
                width=1,
            )

            # Convert normalized coordinates to displayed
            # image coordinates.
            x1 = (
                float(row["x1_norm"])
                * display_width
            )

            y1 = (
                float(row["y1_norm"])
                * display_height
            )

            x2 = (
                float(row["x2_norm"])
                * display_width
            )

            y2 = (
                float(row["y2_norm"])
                * display_height
            )

            local_draw.rectangle(
                [
                    paste_x + x1,
                    paste_y + y1,
                    paste_x + x2,
                    paste_y + y2,
                ],
                outline=BOX_COLOR,
                width=3,
            )

            label = (
                f"{row['file_stem']} | "
                f"{row['class_name']}\n"
                f"Problem: "
                f"{row['boundary_problem']}\n"
                f"Overflow: "
                f"{row['max_overflow_norm']:.6f} "
                f"({row['max_overflow_pixels']:.1f}px)\n"
                f"Raw: {row['raw_label']}"
            )

            local_draw.text(
                (
                    origin_x + 7,
                    origin_y
                    + THUMBNAIL_HEIGHT
                    + 6,
                ),
                label,
                fill=TEXT_COLOR,
                font=font,
            )

            image.close()

        except Exception as exc:
            draw.text(
                (
                    origin_x + 10,
                    origin_y + 10,
                ),
                (
                    "Failed to load\n"
                    f"{row['file_stem']}\n"
                    f"{type(exc).__name__}"
                ),
                fill=TEXT_COLOR,
                font=font,
            )

    OUTPUT_IMAGE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    sheet.save(
        OUTPUT_IMAGE,
        quality=92,
    )

    sheet.close()

    print()
    print(
        f"Boundary review sheet: "
        f"{OUTPUT_IMAGE}"
    )


def print_summary(
    dataframe: pd.DataFrame,
) -> None:
    """
    Print the boundary-violation summary.
    """
    print()
    print("=" * 72)
    print(
        "BOUNDARY ANNOTATION DIAGNOSIS"
    )
    print("=" * 72)

    if dataframe.empty:
        print(
            "No boundary violations found."
        )
        return

    print()
    print(
        f"Boundary-violating boxes: "
        f"{len(dataframe)}"
    )

    print()
    print(
        "PROBLEM DISTRIBUTION"
    )
    print("-" * 72)

    for (
        problem,
        count,
    ) in (
        dataframe[
            "boundary_problem"
        ]
        .value_counts()
        .items()
    ):
        print(
            f"{problem:25} {count}"
        )

    print()
    print(
        "OVERFLOW DISTRIBUTION"
    )
    print("-" * 72)

    overflow = (
        dataframe[
            "max_overflow_pixels"
        ]
    )

    print(
        f"Minimum overflow pixels : "
        f"{overflow.min():.3f}"
    )

    print(
        f"Median overflow pixels  : "
        f"{overflow.median():.3f}"
    )

    print(
        f"Maximum overflow pixels : "
        f"{overflow.max():.3f}"
    )

    print()
    print(
        "CLASS DISTRIBUTION"
    )
    print("-" * 72)

    for (
        class_name,
        count,
    ) in (
        dataframe[
            "class_name"
        ]
        .value_counts()
        .items()
    ):
        print(
            f"{class_name:25} {count}"
        )

    print()
    print(
        "TOP 20 LARGEST OVERFLOWS"
    )
    print("-" * 72)

    top = (
        dataframe
        .sort_values(
            "max_overflow_pixels",
            ascending=False,
        )
        .head(20)
    )

    for _, row in top.iterrows():
        print(
            f"{row['file_stem']:32} "
            f"{row['boundary_problem']:10} "
            f"{row['max_overflow_pixels']:.2f}px"
        )

    print()
    print("=" * 72)
    print(
        "DIAGNOSIS COMPLETE"
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
        "TOWERVISION AI - BOUNDARY ANNOTATION INSPECTION"
    )
    print("=" * 72)
    print()

    classes = load_classes()

    print(
        "Classes:"
    )

    for index, name in enumerate(
        classes
    ):
        print(
            f"  {index}: {name}"
        )

    print()

    dataframe = build_report(
        classes
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8",
    )

    print()
    print(
        f"Report saved: {OUTPUT_CSV}"
    )

    print_summary(
        dataframe
    )

    create_contact_sheet(
        dataframe
    )


if __name__ == "__main__":
    main()