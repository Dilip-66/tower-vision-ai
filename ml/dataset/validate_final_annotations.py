from pathlib import Path
import csv
import json

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

REPORT_DIR = PROJECT_ROOT / "data" / "reports"

REPORT_CSV = REPORT_DIR / "final_annotation_validation.csv"
REPORT_JSON = REPORT_DIR / "final_annotation_validation.json"

CLASS_NAMES = {
    0: "supporting_tower",
    1: "monopole_tower",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

EPSILON = 1e-9


# ============================================================
# HELPERS
# ============================================================

def is_valid_number(value):
    return value == value and abs(value) != float("inf")


def validate_box(class_id, x, y, w, h):
    errors = []

    if class_id not in CLASS_NAMES:
        errors.append("invalid_class_id")

    values = [x, y, w, h]

    if not all(is_valid_number(v) for v in values):
        errors.append("non_finite_coordinate")
        return errors

    if x < -EPSILON or x > 1.0 + EPSILON:
        errors.append("x_center_outside_range")

    if y < -EPSILON or y > 1.0 + EPSILON:
        errors.append("y_center_outside_range")

    if w <= 0:
        errors.append("non_positive_width")

    if h <= 0:
        errors.append("non_positive_height")

    if w > 1.0 + EPSILON:
        errors.append("width_outside_range")

    if h > 1.0 + EPSILON:
        errors.append("height_outside_range")

    x1 = x - w / 2.0
    y1 = y - h / 2.0
    x2 = x + w / 2.0
    y2 = y + h / 2.0

    if x1 < -EPSILON:
        errors.append("box_left_outside_image")

    if y1 < -EPSILON:
        errors.append("box_top_outside_image")

    if x2 > 1.0 + EPSILON:
        errors.append("box_right_outside_image")

    if y2 > 1.0 + EPSILON:
        errors.append("box_bottom_outside_image")

    return errors


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("FINAL ANNOTATION VALIDATION")
    print("=" * 72)

    if not IMAGE_DIR.exists():
        raise FileNotFoundError(
            f"Image directory not found: {IMAGE_DIR}"
        )

    if not LABEL_DIR.exists():
        raise FileNotFoundError(
            f"Final label directory not found: {LABEL_DIR}"
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    image_files = sorted(
        [
            path
            for path in IMAGE_DIR.iterdir()
            if path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )

    label_files = sorted(
        [
            path
            for path in LABEL_DIR.glob("*.txt")
            if path.name.lower() != "classes.txt"
        ]
    )

    image_map = {
        path.stem: path
        for path in image_files
    }

    label_map = {
        path.stem: path
        for path in label_files
    }

    all_stems = sorted(
        set(image_map.keys()) | set(label_map.keys())
    )

    report_rows = []

    missing_labels = 0
    missing_images = 0
    invalid_images = 0
    valid_images = 0
    validation_errors = 0
    valid_boxes = 0

    class_counts = {
        0: 0,
        1: 0,
    }

    for stem in all_stems:

        image_exists = stem in image_map
        label_exists = stem in label_map

        errors = []
        line_count = 0
        valid_box_count = 0

        if not image_exists:
            missing_images += 1
            errors.append("missing_image")

        if not label_exists:
            missing_labels += 1
            errors.append("missing_label")

        if label_exists:

            label_path = label_map[stem]

            with label_path.open(
                "r",
                encoding="utf-8"
            ) as f:
                lines = f.readlines()

            for line_number, raw_line in enumerate(
                lines,
                start=1
            ):

                stripped = raw_line.strip()

                if not stripped:
                    continue

                line_count += 1

                parts = stripped.split()

                if len(parts) != 5:
                    errors.append(
                        f"line_{line_number}:expected_5_values"
                    )
                    continue

                try:
                    class_id = int(parts[0])

                    x = float(parts[1])
                    y = float(parts[2])
                    w = float(parts[3])
                    h = float(parts[4])

                except ValueError:
                    errors.append(
                        f"line_{line_number}:non_numeric_value"
                    )
                    continue

                box_errors = validate_box(
                    class_id,
                    x,
                    y,
                    w,
                    h,
                )

                if box_errors:
                    for error in box_errors:
                        errors.append(
                            f"line_{line_number}:{error}"
                        )
                else:
                    valid_box_count += 1

                    if class_id in class_counts:
                        class_counts[class_id] += 1

        if errors:
            invalid_images += 1
            validation_errors += len(errors)
            status = "invalid"
        else:
            valid_images += 1
            valid_boxes += valid_box_count
            status = "valid"

        report_rows.append(
            {
                "file_stem": stem,
                "image_file": (
                    image_map[stem].name
                    if image_exists
                    else ""
                ),
                "label_file": (
                    label_map[stem].name
                    if label_exists
                    else ""
                ),
                "image_exists": image_exists,
                "label_exists": label_exists,
                "line_count": line_count,
                "valid_box_count": valid_box_count,
                "status": status,
                "errors": ";".join(errors),
            }
        )

    # ========================================================
    # CSV REPORT
    # ========================================================

    with REPORT_CSV.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        fieldnames = [
            "file_stem",
            "image_file",
            "label_file",
            "image_exists",
            "label_exists",
            "line_count",
            "valid_box_count",
            "status",
            "errors",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(report_rows)

    # ========================================================
    # JSON REPORT
    # ========================================================

    json_report = {
        "summary": {
            "images": len(image_files),
            "labels": len(label_files),
            "missing_labels": missing_labels,
            "missing_images": missing_images,
            "invalid_images": invalid_images,
            "validation_errors": validation_errors,
            "valid_images": valid_images,
            "valid_boxes": valid_boxes,
        },
        "class_distribution": {
            "supporting_tower": class_counts[0],
            "monopole_tower": class_counts[1],
        },
        "files": report_rows,
    }

    with REPORT_JSON.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            json_report,
            f,
            indent=2,
        )

    # ========================================================
    # TERMINAL SUMMARY
    # ========================================================

    print()
    print(f"Images             : {len(image_files)}")
    print(f"Labels             : {len(label_files)}")
    print(f"Missing labels     : {missing_labels}")
    print(f"Missing images     : {missing_images}")
    print(f"Invalid images     : {invalid_images}")
    print(f"Validation errors  : {validation_errors}")
    print(f"Valid boxes        : {valid_boxes}")

    print()
    print("CLASS DISTRIBUTION")
    print("-" * 72)
    print(
        f"supporting_tower : {class_counts[0]}"
    )
    print(
        f"monopole_tower   : {class_counts[1]}"
    )

    print()
    if invalid_images == 0 and validation_errors == 0:
        print("=" * 72)
        print("FINAL ANNOTATIONS: VALID")
        print("=" * 72)
        print()
        print("All annotation files passed structural validation.")
    else:
        print("=" * 72)
        print("FINAL ANNOTATIONS: REVIEW REQUIRED")
        print("=" * 72)

    print()
    print(f"Report CSV  : {REPORT_CSV}")
    print(f"Report JSON : {REPORT_JSON}")


if __name__ == "__main__":
    main()