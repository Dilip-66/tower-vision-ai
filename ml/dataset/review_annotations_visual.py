from pathlib import Path
import math
import csv
import json

import cv2


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation"
    / "images"
)

LABEL_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation_final"
    / "labels"
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "reports"
    / "annotation_visual_qa"
)

CONTACT_SHEET_DIR = OUTPUT_ROOT / "contact_sheets"

SUMMARY_CSV = OUTPUT_ROOT / "annotation_visual_qa.csv"
SUMMARY_JSON = OUTPUT_ROOT / "annotation_visual_qa.json"


# ============================================================
# SETTINGS
# ============================================================

# Contact sheet layout
COLUMNS = 5
ROWS = 5

# Size of each cell in the contact sheet
CELL_WIDTH = 300
CELL_HEIGHT = 260

# Box thickness
BOX_THICKNESS = 3

# Font
FONT = cv2.FONT_HERSHEY_SIMPLEX

# Class names
CLASS_NAMES = {
    0: "supporting_tower",
    1: "monopole_tower",
}


# ============================================================
# HELPERS
# ============================================================

def get_image_files():
    extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
    }

    return sorted(
        [
            path
            for path in IMAGE_DIR.iterdir()
            if path.is_file()
            and path.suffix.lower() in extensions
        ]
    )


def read_yolo_labels(label_path):
    boxes = []

    with label_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for line_number, raw_line in enumerate(lines, start=1):

        line = raw_line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) != 5:
            continue

        try:
            class_id = int(parts[0])

            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])

        except ValueError:
            continue

        boxes.append(
            {
                "line_number": line_number,
                "class_id": class_id,
                "class_name": CLASS_NAMES.get(
                    class_id,
                    f"unknown_{class_id}",
                ),
                "x_center": x_center,
                "y_center": y_center,
                "width": width,
                "height": height,
            }
        )

    return boxes


def yolo_to_pixels(box, image_width, image_height):

    x_center = box["x_center"]
    y_center = box["y_center"]
    width = box["width"]
    height = box["height"]

    x1 = int(round(
        (x_center - width / 2.0) * image_width
    ))

    y1 = int(round(
        (y_center - height / 2.0) * image_height
    ))

    x2 = int(round(
        (x_center + width / 2.0) * image_width
    ))

    y2 = int(round(
        (y_center + height / 2.0) * image_height
    ))

    # Keep drawing safely inside the image.
    x1 = max(0, min(image_width - 1, x1))
    y1 = max(0, min(image_height - 1, y1))
    x2 = max(0, min(image_width - 1, x2))
    y2 = max(0, min(image_height - 1, y2))

    return x1, y1, x2, y2


def resize_to_cell(image):
    h, w = image.shape[:2]

    if w <= 0 or h <= 0:
        return None

    scale = min(
        CELL_WIDTH / w,
        CELL_HEIGHT / h,
    )

    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = cv2.resize(
        image,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA,
    )

    canvas = 255 * (
        __import__("numpy").ones(
            (CELL_HEIGHT, CELL_WIDTH, 3),
            dtype="uint8",
        )
    )

    x_offset = (CELL_WIDTH - new_w) // 2
    y_offset = (CELL_HEIGHT - new_h) // 2

    canvas[
        y_offset:y_offset + new_h,
        x_offset:x_offset + new_w
    ] = resized

    return canvas


def add_label_text(
    image,
    text,
    position,
    font_scale=0.48,
    thickness=1,
):
    cv2.putText(
        image,
        text,
        position,
        FONT,
        font_scale,
        (0, 0, 0),
        thickness + 2,
        cv2.LINE_AA,
    )

    cv2.putText(
        image,
        text,
        position,
        FONT,
        font_scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def draw_annotation(image, box, image_width, image_height):

    x1, y1, x2, y2 = yolo_to_pixels(
        box,
        image_width,
        image_height,
    )

    class_name = box["class_name"]

    # Different colors make the two classes visually distinct.
    if box["class_id"] == 0:
        box_color = (255, 120, 0)
    else:
        box_color = (0, 120, 255)

    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        box_color,
        BOX_THICKNESS,
    )

    text = class_name

    text_y = max(20, y1 - 8)

    cv2.putText(
        image,
        text,
        (x1, text_y),
        FONT,
        0.65,
        box_color,
        2,
        cv2.LINE_AA,
    )

    return x1, y1, x2, y2


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("VISUAL ANNOTATION QA")
    print("=" * 72)

    if not IMAGE_DIR.exists():
        raise FileNotFoundError(
            f"Image directory not found: {IMAGE_DIR}"
        )

    if not LABEL_DIR.exists():
        raise FileNotFoundError(
            f"Label directory not found: {LABEL_DIR}"
        )

    CONTACT_SHEET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    image_files = get_image_files()

    if not image_files:
        raise RuntimeError("No images found.")

    # --------------------------------------------------------
    # Summary structures
    # --------------------------------------------------------

    rows_per_sheet = COLUMNS * ROWS

    summary_rows = []

    total_boxes = 0
    supporting_count = 0
    monopole_count = 0

    border_touching_boxes = 0
    very_small_boxes = 0
    very_large_boxes = 0

    sheet_images = []
    sheet_number = 1

    # --------------------------------------------------------
    # Process each image
    # --------------------------------------------------------

    for index, image_path in enumerate(image_files):

        label_path = LABEL_DIR / f"{image_path.stem}.txt"

        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_COLOR,
        )

        if image is None:
            summary_rows.append(
                {
                    "file_stem": image_path.stem,
                    "image_file": image_path.name,
                    "label_file": label_path.name,
                    "image_width": "",
                    "image_height": "",
                    "box_count": "",
                    "classes": "",
                    "status": "image_read_failed",
                    "border_touching": "",
                    "box_area_ratio": "",
                }
            )
            continue

        image_height, image_width = image.shape[:2]

        boxes = []

        if label_path.exists():
            boxes = read_yolo_labels(label_path)

        annotated = image.copy()

        class_names_in_image = []
        border_touching = False
        area_ratios = []

        for box in boxes:

            x1, y1, x2, y2 = draw_annotation(
                annotated,
                box,
                image_width,
                image_height,
            )

            class_id = box["class_id"]
            class_name = box["class_name"]

            class_names_in_image.append(class_name)

            total_boxes += 1

            if class_id == 0:
                supporting_count += 1
            elif class_id == 1:
                monopole_count += 1

            # ------------------------------------------------
            # Pixel-space analysis for visual review
            # ------------------------------------------------

            box_width_pixels = max(
                0,
                x2 - x1,
            )

            box_height_pixels = max(
                0,
                y2 - y1,
            )

            area_ratio = (
                box_width_pixels
                * box_height_pixels
            ) / (
                image_width
                * image_height
            )

            area_ratios.append(area_ratio)

            # Touching image border
            touches_border = (
                x1 <= 0
                or y1 <= 0
                or x2 >= image_width - 1
                or y2 >= image_height - 1
            )

            if touches_border:
                border_touching = True
                border_touching_boxes += 1

            # Extremely small relative boxes
            if area_ratio < 0.01:
                very_small_boxes += 1

            # Extremely large relative boxes
            if area_ratio > 0.90:
                very_large_boxes += 1

        # ----------------------------------------------------
        # Add filename and image index to annotated image
        # ----------------------------------------------------

        footer = (
            f"{index + 1}/{len(image_files)}  "
            f"{image_path.stem}"
        )

        add_label_text(
            annotated,
            footer,
            (8, image_height - 10),
            font_scale=0.42,
            thickness=1,
        )

        resized = resize_to_cell(annotated)

        if resized is not None:
            sheet_images.append(resized)

        status = (
            "annotated"
            if boxes
            else "no_boxes"
        )

        summary_rows.append(
            {
                "file_stem": image_path.stem,
                "image_file": image_path.name,
                "label_file": label_path.name,
                "image_width": image_width,
                "image_height": image_height,
                "box_count": len(boxes),
                "classes": "|".join(
                    class_names_in_image
                ),
                "status": status,
                "border_touching": border_touching,
                "box_area_ratio": (
                    max(area_ratios)
                    if area_ratios
                    else ""
                ),
            }
        )

        # ----------------------------------------------------
        # Write contact sheet every N images
        # ----------------------------------------------------

        if len(sheet_images) == rows_per_sheet:
            sheet_width = COLUMNS * CELL_WIDTH
            sheet_height = ROWS * CELL_HEIGHT

            sheet = __import__("numpy").ones(
                (
                    sheet_height,
                    sheet_width,
                    3,
                ),
                dtype="uint8",
            ) * 255

            for i, cell in enumerate(sheet_images):
                row = i // COLUMNS
                col = i % COLUMNS

                y1 = row * CELL_HEIGHT
                y2 = y1 + CELL_HEIGHT

                x1 = col * CELL_WIDTH
                x2 = x1 + CELL_WIDTH

                sheet[
                    y1:y2,
                    x1:x2
                ] = cell

            output_path = (
                CONTACT_SHEET_DIR
                / f"annotations_{sheet_number:02d}.jpg"
            )

            cv2.imwrite(
                str(output_path),
                sheet,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    92,
                ],
            )

            print(
                f"Created contact sheet: "
                f"{output_path.name}"
            )

            sheet_images = []
            sheet_number += 1

    # --------------------------------------------------------
    # Final partial sheet
    # --------------------------------------------------------

    if sheet_images:

        sheet_rows = math.ceil(
            len(sheet_images) / COLUMNS
        )

        sheet_width = COLUMNS * CELL_WIDTH
        sheet_height = sheet_rows * CELL_HEIGHT

        sheet = __import__("numpy").ones(
            (
                sheet_height,
                sheet_width,
                3,
            ),
            dtype="uint8",
        ) * 255

        for i, cell in enumerate(sheet_images):

            row = i // COLUMNS
            col = i % COLUMNS

            y1 = row * CELL_HEIGHT
            y2 = y1 + CELL_HEIGHT

            x1 = col * CELL_WIDTH
            x2 = x1 + CELL_WIDTH

            sheet[
                y1:y2,
                x1:x2
            ] = cell

        output_path = (
            CONTACT_SHEET_DIR
            / f"annotations_{sheet_number:02d}.jpg"
        )

        cv2.imwrite(
            str(output_path),
            sheet,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                92,
            ],
        )

        print(
            f"Created contact sheet: "
            f"{output_path.name}"
        )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    with SUMMARY_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "file_stem",
            "image_file",
            "label_file",
            "image_width",
            "image_height",
            "box_count",
            "classes",
            "status",
            "border_touching",
            "box_area_ratio",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(summary_rows)

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    json_report = {
        "summary": {
            "images_processed": len(image_files),
            "total_boxes": total_boxes,
            "supporting_tower": supporting_count,
            "monopole_tower": monopole_count,
            "border_touching_boxes": border_touching_boxes,
            "very_small_boxes": very_small_boxes,
            "very_large_boxes": very_large_boxes,
            "contact_sheet_columns": COLUMNS,
            "contact_sheet_rows": ROWS,
            "cell_width": CELL_WIDTH,
            "cell_height": CELL_HEIGHT,
        },
        "files": summary_rows,
    }

    with SUMMARY_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            json_report,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # Terminal summary
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("VISUAL QA SUMMARY")
    print("=" * 72)

    print(
        f"Images processed       : {len(image_files)}"
    )
    print(
        f"Total boxes            : {total_boxes}"
    )
    print(
        f"supporting_tower       : {supporting_count}"
    )
    print(
        f"monopole_tower         : {monopole_count}"
    )
    print(
        f"Border-touching boxes  : {border_touching_boxes}"
    )
    print(
        f"Very small boxes       : {very_small_boxes}"
    )
    print(
        f"Very large boxes       : {very_large_boxes}"
    )

    print()
    print(
        f"Contact sheets         : "
        f"{CONTACT_SHEET_DIR}"
    )
    print(
        f"CSV report             : "
        f"{SUMMARY_CSV}"
    )
    print(
        f"JSON report            : "
        f"{SUMMARY_JSON}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()