from pathlib import Path
from collections import defaultdict
import csv
import json


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = PROJECT_ROOT / "data" / "processed"

IMAGES_ROOT = DATASET_ROOT / "images"
LABELS_ROOT = DATASET_ROOT / "labels"

SPLITS = ["train", "val", "test"]

REPORT_DIR = PROJECT_ROOT / "data" / "reports"

REPORT_CSV = REPORT_DIR / "final_dataset_validation.csv"
REPORT_JSON = REPORT_DIR / "final_dataset_validation.json"

EXPECTED_CLASSES = {
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


# ============================================================
# HELPERS
# ============================================================

def get_images(split):
    image_dir = IMAGES_ROOT / split

    if not image_dir.exists():
        raise FileNotFoundError(
            f"Missing image directory: {image_dir}"
        )

    return sorted(
        [
            path
            for path in image_dir.iterdir()
            if path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )


def get_labels(split):
    label_dir = LABELS_ROOT / split

    if not label_dir.exists():
        raise FileNotFoundError(
            f"Missing label directory: {label_dir}"
        )

    return sorted(
        [
            path
            for path in label_dir.glob("*.txt")
            if path.name.lower() != "classes.txt"
        ]
    )


def parse_labels(label_path):
    errors = []
    boxes = []

    with label_path.open(
        "r",
        encoding="utf-8",
    ) as f:

        for line_number, raw_line in enumerate(
            f.readlines(),
            start=1,
        ):

            line = raw_line.strip()

            if not line:
                continue

            parts = line.split()

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
                    f"line_{line_number}:non_numeric"
                )
                continue

            if class_id not in EXPECTED_CLASSES:
                errors.append(
                    f"line_{line_number}:invalid_class_id"
                )

            if not (0.0 <= x <= 1.0):
                errors.append(
                    f"line_{line_number}:x_out_of_range"
                )

            if not (0.0 <= y <= 1.0):
                errors.append(
                    f"line_{line_number}:y_out_of_range"
                )

            if not (0.0 < w <= 1.0):
                errors.append(
                    f"line_{line_number}:width_out_of_range"
                )

            if not (0.0 < h <= 1.0):
                errors.append(
                    f"line_{line_number}:height_out_of_range"
                )

            x1 = x - w / 2.0
            y1 = y - h / 2.0
            x2 = x + w / 2.0
            y2 = y + h / 2.0

            if x1 < 0.0:
                errors.append(
                    f"line_{line_number}:left_outside"
                )

            if y1 < 0.0:
                errors.append(
                    f"line_{line_number}:top_outside"
                )

            if x2 > 1.0:
                errors.append(
                    f"line_{line_number}:right_outside"
                )

            if y2 > 1.0:
                errors.append(
                    f"line_{line_number}:bottom_outside"
                )

            boxes.append(
                {
                    "class_id": class_id,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                }
            )

    return boxes, errors


def source_group_from_stem(stem):
    if "_frame_" not in stem:
        return stem

    return stem.split("_frame_")[0]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("TOWERVISION AI - FINAL DATASET VALIDATION")
    print("=" * 72)

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_images = 0
    total_labels = 0
    total_boxes = 0

    total_missing_labels = 0
    total_missing_images = 0
    total_invalid_files = 0
    total_errors = 0

    overall_class_counts = {
        0: 0,
        1: 0,
    }

    split_summary = {}

    # Track every file and source globally.
    global_file_splits = {}
    global_source_splits = defaultdict(set)

    report_rows = []

    # --------------------------------------------------------
    # Validate each split
    # --------------------------------------------------------

    for split in SPLITS:

        images = get_images(split)
        labels = get_labels(split)

        image_map = {
            path.stem: path
            for path in images
        }

        label_map = {
            path.stem: path
            for path in labels
        }

        image_stems = set(image_map)
        label_stems = set(label_map)

        missing_labels = sorted(
            image_stems - label_stems
        )

        missing_images = sorted(
            label_stems - image_stems
        )

        split_class_counts = {
            0: 0,
            1: 0,
        }

        split_boxes = 0
        split_invalid = 0
        split_errors = 0

        # ----------------------------------------------------
        # Validate image/label pairs
        # ----------------------------------------------------

        for stem in sorted(
            image_stems | label_stems
        ):

            image_exists = stem in image_map
            label_exists = stem in label_map

            errors = []
            box_count = 0

            class_counts = {
                0: 0,
                1: 0,
            }

            if not image_exists:
                errors.append("missing_image")

            if not label_exists:
                errors.append("missing_label")

            if label_exists:

                boxes, label_errors = parse_labels(
                    label_map[stem]
                )

                errors.extend(label_errors)

                box_count = len(boxes)

                for box in boxes:

                    class_id = box["class_id"]

                    if class_id in class_counts:
                        class_counts[class_id] += 1

            if errors:
                status = "invalid"

                split_invalid += 1
                split_errors += len(errors)

            else:
                status = "valid"

            split_boxes += box_count

            for class_id in (
                0,
                1,
            ):

                split_class_counts[
                    class_id
                ] += class_counts[class_id]

                overall_class_counts[
                    class_id
                ] += class_counts[class_id]

            source_group = (
                source_group_from_stem(stem)
            )

            global_source_splits[
                source_group
            ].add(split)

            previous_split = (
                global_file_splits.get(stem)
            )

            if (
                previous_split is not None
                and previous_split != split
            ):
                errors.append(
                    "same_file_in_multiple_splits"
                )

            global_file_splits[
                stem
            ] = split

            report_rows.append(
                {
                    "split": split,
                    "file_stem": stem,
                    "image_exists": image_exists,
                    "label_exists": label_exists,
                    "box_count": box_count,
                    "supporting_tower": class_counts[0],
                    "monopole_tower": class_counts[1],
                    "status": (
                        "invalid"
                        if errors
                        else "valid"
                    ),
                    "errors": ";".join(errors),
                }
            )

        total_images += len(images)
        total_labels += len(labels)
        total_boxes += split_boxes

        total_missing_labels += len(
            missing_labels
        )

        total_missing_images += len(
            missing_images
        )

        total_invalid_files += split_invalid
        total_errors += split_errors

        split_summary[split] = {
            "images": len(images),
            "labels": len(labels),
            "boxes": split_boxes,
            "missing_labels": len(
                missing_labels
            ),
            "missing_images": len(
                missing_images
            ),
            "invalid_files": split_invalid,
            "validation_errors": split_errors,
            "supporting_tower": split_class_counts[0],
            "monopole_tower": split_class_counts[1],
        }

    # --------------------------------------------------------
    # Source leakage check
    # --------------------------------------------------------

    source_leakage = {
        source: sorted(splits)
        for source, splits
        in global_source_splits.items()
        if len(splits) > 1
    }

    # --------------------------------------------------------
    # Global duplicate filename check
    # --------------------------------------------------------

    filename_duplicate_groups = defaultdict(
        list
    )

    for stem, split in global_file_splits.items():
        filename_duplicate_groups[
            stem
        ].append(split)

    duplicate_filename_groups = {
        stem: sorted(set(splits))
        for stem, splits
        in filename_duplicate_groups.items()
        if len(set(splits)) > 1
    }

    # --------------------------------------------------------
    # CSV report
    # --------------------------------------------------------

    with REPORT_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "split",
            "file_stem",
            "image_exists",
            "label_exists",
            "box_count",
            "supporting_tower",
            "monopole_tower",
            "status",
            "errors",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(report_rows)

    # --------------------------------------------------------
    # JSON report
    # --------------------------------------------------------

    json_report = {
        "summary": {
            "images": total_images,
            "labels": total_labels,
            "boxes": total_boxes,
            "missing_labels": total_missing_labels,
            "missing_images": total_missing_images,
            "invalid_files": total_invalid_files,
            "validation_errors": total_errors,
            "source_leakage_groups": len(
                source_leakage
            ),
            "duplicate_filename_groups": len(
                duplicate_filename_groups
            ),
        },
        "class_distribution": {
            "supporting_tower":
                overall_class_counts[0],
            "monopole_tower":
                overall_class_counts[1],
        },
        "splits": split_summary,
        "source_leakage": source_leakage,
        "duplicate_filename_groups":
            duplicate_filename_groups,
    }

    with REPORT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            json_report,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # Terminal output
    # --------------------------------------------------------

    print()
    print("SPLIT VALIDATION")
    print("-" * 72)

    for split in SPLITS:

        data = split_summary[split]

        print(
            f"{split:5s} : "
            f"{data['images']:3d} images | "
            f"{data['labels']:3d} labels | "
            f"{data['boxes']:3d} boxes | "
            f"supporting={data['supporting_tower']:3d} | "
            f"monopole={data['monopole_tower']:2d} | "
            f"errors={data['validation_errors']}"
        )

    print()
    print("GLOBAL VALIDATION")
    print("-" * 72)

    print(
        f"Images                 : {total_images}"
    )

    print(
        f"Labels                 : {total_labels}"
    )

    print(
        f"Boxes                  : {total_boxes}"
    )

    print(
        f"Missing labels        : {total_missing_labels}"
    )

    print(
        f"Missing images        : {total_missing_images}"
    )

    print(
        f"Invalid files         : {total_invalid_files}"
    )

    print(
        f"Validation errors     : {total_errors}"
    )

    print(
        f"Source leakage groups : {len(source_leakage)}"
    )

    print(
        f"Duplicate filename groups : "
        f"{len(duplicate_filename_groups)}"
    )

    print()
    print("OVERALL CLASS DISTRIBUTION")
    print("-" * 72)

    print(
        f"supporting_tower : "
        f"{overall_class_counts[0]}"
    )

    print(
        f"monopole_tower   : "
        f"{overall_class_counts[1]}"
    )

    print()

    if (
        total_missing_labels == 0
        and total_missing_images == 0
        and total_invalid_files == 0
        and total_errors == 0
        and len(source_leakage) == 0
        and len(duplicate_filename_groups) == 0
        and total_images == 209
        and total_labels == 209
    ):
        print("=" * 72)
        print("FINAL DATASET: VALID")
        print("=" * 72)
        print()
        print(
            "The processed YOLO dataset is ready "
            "for model training."
        )
    else:
        print("=" * 72)
        print("FINAL DATASET: REVIEW REQUIRED")
        print("=" * 72)

    print()
    print(f"CSV report  : {REPORT_CSV}")
    print(f"JSON report : {REPORT_JSON}")


if __name__ == "__main__":
    main()