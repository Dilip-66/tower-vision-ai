from pathlib import Path
import json


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_DIR = PROJECT_ROOT / "data" / "interim" / "annotation" / "images"

INPUT_LABEL_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation_repaired"
    / "labels"
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotation_final"
)

OUTPUT_LABEL_DIR = OUTPUT_ROOT / "labels"

REPORT_DIR = PROJECT_ROOT / "data" / "reports"

REPORT_CSV = REPORT_DIR / "final_boundary_annotation_repair.csv"
REPORT_JSON = REPORT_DIR / "final_boundary_annotation_repair.json"

EPSILON = 1e-9


# ============================================================
# HELPERS
# ============================================================

def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def nearly_equal(a: float, b: float, eps: float = EPSILON) -> bool:
    return abs(a - b) <= eps


def process_label_file(input_path: Path, output_path: Path):
    repaired_boxes = 0
    unchanged_boxes = 0
    malformed_lines = 0
    manual_review_boxes = 0
    max_overflow = 0.0
    changes = []

    output_lines = []

    with input_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        if not stripped:
            continue

        parts = stripped.split()

        if len(parts) != 5:
            malformed_lines += 1
            output_lines.append(stripped)
            continue

        try:
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
        except ValueError:
            malformed_lines += 1
            output_lines.append(stripped)
            continue

        # Original YOLO coordinates
        x1 = x_center - width / 2.0
        y1 = y_center - height / 2.0
        x2 = x_center + width / 2.0
        y2 = y_center + height / 2.0

        original_corners = (x1, y1, x2, y2)

        # Measure overflow before correction.
        overflows = [
            max(0.0, -x1),
            max(0.0, -y1),
            max(0.0, x2 - 1.0),
            max(0.0, y2 - 1.0),
        ]

        current_max_overflow = max(overflows)
        max_overflow = max(max_overflow, current_max_overflow)

        # This script is intentionally conservative.
        # Any tiny boundary overflow is clipped.
        clipped_x1 = clamp(x1)
        clipped_y1 = clamp(y1)
        clipped_x2 = clamp(x2)
        clipped_y2 = clamp(y2)

        # Recompute YOLO coordinates from clipped corners.
        new_x_center = (clipped_x1 + clipped_x2) / 2.0
        new_y_center = (clipped_y1 + clipped_y2) / 2.0
        new_width = clipped_x2 - clipped_x1
        new_height = clipped_y2 - clipped_y1

        # Protect against numerical noise after conversion.
        new_x_center = clamp(new_x_center)
        new_y_center = clamp(new_y_center)
        new_width = max(0.0, min(1.0, new_width))
        new_height = max(0.0, min(1.0, new_height))

        changed = not (
            nearly_equal(x_center, new_x_center)
            and nearly_equal(y_center, new_y_center)
            and nearly_equal(width, new_width)
            and nearly_equal(height, new_height)
        )

        if changed:
            repaired_boxes += 1

            changes.append(
                {
                    "line": line_number,
                    "class_id": class_id,
                    "original": {
                        "x_center": x_center,
                        "y_center": y_center,
                        "width": width,
                        "height": height,
                    },
                    "repaired": {
                        "x_center": new_x_center,
                        "y_center": new_y_center,
                        "width": new_width,
                        "height": new_height,
                    },
                    "original_corners": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    },
                    "clipped_corners": {
                        "x1": clipped_x1,
                        "y1": clipped_y1,
                        "x2": clipped_x2,
                        "y2": clipped_y2,
                    },
                }
            )
        else:
            unchanged_boxes += 1

        # Write with 8 decimal places to avoid introducing
        # a new floating-point boundary overflow.
        output_lines.append(
            f"{class_id} "
            f"{new_x_center:.8f} "
            f"{new_y_center:.8f} "
            f"{new_width:.8f} "
            f"{new_height:.8f}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
        if output_lines:
            f.write("\n")

    return {
        "file_stem": input_path.stem,
        "changed": changed if 'changed' in locals() else False,
        "repaired_boxes": repaired_boxes,
        "unchanged_boxes": unchanged_boxes,
        "malformed_lines": malformed_lines,
        "manual_review_boxes": manual_review_boxes,
        "max_overflow": max_overflow,
        "changes": changes,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 72)
    print("FINAL BOUNDARY ANNOTATION CORRECTION")
    print("=" * 72)

    if not IMAGE_DIR.exists():
        raise FileNotFoundError(f"Image directory not found: {IMAGE_DIR}")

    if not INPUT_LABEL_DIR.exists():
        raise FileNotFoundError(
            f"Input label directory not found: {INPUT_LABEL_DIR}"
        )

    OUTPUT_LABEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    label_files = sorted(INPUT_LABEL_DIR.glob("*.txt"))

    # Exclude classes.txt if present.
    label_files = [
        path for path in label_files
        if path.name.lower() != "classes.txt"
    ]

    image_stems = {
        path.stem
        for path in IMAGE_DIR.iterdir()
        if path.is_file()
    }

    report_rows = []

    total_repaired_boxes = 0
    total_unchanged_boxes = 0
    total_malformed_lines = 0
    total_manual_review = 0
    changed_files = 0
    unchanged_files = 0
    maximum_overflow = 0.0

    for input_path in label_files:
        output_path = OUTPUT_LABEL_DIR / input_path.name

        result = process_label_file(
            input_path=input_path,
            output_path=output_path,
        )

        total_repaired_boxes += result["repaired_boxes"]
        total_unchanged_boxes += result["unchanged_boxes"]
        total_malformed_lines += result["malformed_lines"]
        total_manual_review += result["manual_review_boxes"]
        maximum_overflow = max(
            maximum_overflow,
            result["max_overflow"],
        )

        if result["repaired_boxes"] > 0:
            changed_files += 1
        else:
            unchanged_files += 1

        report_rows.append(
            {
                "file_stem": result["file_stem"],
                "changed": result["repaired_boxes"] > 0,
                "repaired_boxes": result["repaired_boxes"],
                "unchanged_boxes": result["unchanged_boxes"],
                "malformed_lines": result["malformed_lines"],
                "manual_review_boxes": result["manual_review_boxes"],
                "max_overflow": result["max_overflow"],
                "image_exists": result["file_stem"] in image_stems,
            }
        )

    # CSV
    import csv

    with REPORT_CSV.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_stem",
                "changed",
                "repaired_boxes",
                "unchanged_boxes",
                "malformed_lines",
                "manual_review_boxes",
                "max_overflow",
                "image_exists",
            ],
        )
        writer.writeheader()
        writer.writerows(report_rows)

    # JSON
    report_json = {
        "summary": {
            "annotation_files": len(label_files),
            "changed_files": changed_files,
            "unchanged_files": unchanged_files,
            "repaired_boxes": total_repaired_boxes,
            "unchanged_boxes": total_unchanged_boxes,
            "malformed_lines": total_malformed_lines,
            "manual_review_boxes": total_manual_review,
            "maximum_overflow": maximum_overflow,
        },
        "files": report_rows,
    }

    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    print()
    print(f"Annotation files       : {len(label_files)}")
    print(f"Changed files         : {changed_files}")
    print(f"Unchanged files       : {unchanged_files}")
    print(f"Repaired boxes        : {total_repaired_boxes}")
    print(f"Manual review boxes   : {total_manual_review}")
    print(f"Malformed lines       : {total_malformed_lines}")
    print(f"Maximum overflow      : {maximum_overflow:.9f}")

    print()
    print(f"Final labels          : {OUTPUT_LABEL_DIR}")
    print(f"Report CSV            : {REPORT_CSV}")
    print(f"Report JSON           : {REPORT_JSON}")

    print("=" * 72)


if __name__ == "__main__":
    main()