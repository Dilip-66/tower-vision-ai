from pathlib import Path
import csv
import json
import hashlib
from collections import defaultdict

import cv2
import numpy as np


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

GROUP_CSV = REPORT_DIR / "source_group_analysis.csv"
GROUP_JSON = REPORT_DIR / "source_group_analysis.json"

DUPLICATE_CSV = REPORT_DIR / "cross_source_duplicate_analysis.csv"
DUPLICATE_JSON = REPORT_DIR / "cross_source_duplicate_analysis.json"


# ============================================================
# CLASS CONFIGURATION
# ============================================================

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


# ============================================================
# IMAGE HASHING
# ============================================================

def pixel_hash(image):
    """
    Hash the decoded pixel data.

    This catches exact duplicates even when the files themselves
    have different filenames or compression metadata.
    """

    if image is None:
        return None

    contiguous = np.ascontiguousarray(image)

    return hashlib.sha256(
        contiguous.tobytes()
    ).hexdigest()


def dhash(image, hash_size=8):
    """
    Compute a simple perceptual difference hash.

    This is only used to identify candidates for manual review.
    It is NOT automatically treated as a duplicate.
    """

    if image is None:
        return None

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    resized = cv2.resize(
        gray,
        (hash_size + 1, hash_size),
        interpolation=cv2.INTER_AREA,
    )

    difference = resized[:, 1:] > resized[:, :-1]

    value = 0

    for bit in difference.flatten():
        value = (value << 1) | int(bit)

    return value


def hamming_distance(a, b):
    return (a ^ b).bit_count()


# ============================================================
# LABEL READING
# ============================================================

def read_labels(label_path):

    classes = []
    box_count = 0

    if not label_path.exists():
        return classes, box_count

    with label_path.open(
        "r",
        encoding="utf-8",
    ) as f:

        for raw_line in f:

            line = raw_line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) != 5:
                continue

            try:
                class_id = int(parts[0])
            except ValueError:
                continue

            classes.append(class_id)
            box_count += 1

    return classes, box_count


# ============================================================
# SOURCE GROUP EXTRACTION
# ============================================================

def extract_source_group(file_stem):

    """
    SOURCE_0001_frame_00
    SOURCE_0001_frame_01

    both become:

    SOURCE_0001
    """

    parts = file_stem.split("_")

    if len(parts) >= 2 and parts[0] == "SOURCE":
        return f"SOURCE_{parts[1]}"

    return "UNKNOWN"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("TOWERVISION AI - SOURCE GROUP ANALYSIS")
    print("=" * 72)

    if not IMAGE_DIR.exists():
        raise FileNotFoundError(
            f"Image directory not found: {IMAGE_DIR}"
        )

    if not LABEL_DIR.exists():
        raise FileNotFoundError(
            f"Label directory not found: {LABEL_DIR}"
        )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Find images
    # --------------------------------------------------------

    image_files = sorted(
        [
            path
            for path in IMAGE_DIR.iterdir()
            if path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )

    if not image_files:
        raise RuntimeError(
            "No annotation images found."
        )

    # --------------------------------------------------------
    # Source groups
    # --------------------------------------------------------

    groups = defaultdict(list)

    exact_hash_groups = defaultdict(list)

    image_metadata = {}

    total_boxes = 0

    for image_path in image_files:

        stem = image_path.stem

        source_group = extract_source_group(stem)

        label_path = (
            LABEL_DIR
            / f"{stem}.txt"
        )

        classes, box_count = read_labels(
            label_path
        )

        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_COLOR,
        )

        if image is None:
            raise RuntimeError(
                f"Unable to read image: {image_path}"
            )

        height, width = image.shape[:2]

        exact_hash = pixel_hash(image)
        perceptual_hash = dhash(image)

        class_names = [
            CLASS_NAMES.get(
                class_id,
                f"unknown_{class_id}",
            )
            for class_id in classes
        ]

        unique_class_ids = sorted(
            set(classes)
        )

        record = {
            "file_stem": stem,
            "image_file": image_path.name,
            "label_file": label_path.name,
            "source_group": source_group,
            "frame_index": (
                stem.split("_frame_")[-1]
                if "_frame_" in stem
                else ""
            ),
            "width": width,
            "height": height,
            "box_count": box_count,
            "class_ids": unique_class_ids,
            "class_names": class_names,
            "exact_hash": exact_hash,
            "dhash": perceptual_hash,
        }

        groups[source_group].append(record)

        exact_hash_groups[exact_hash].append(
            record
        )

        image_metadata[stem] = record

        total_boxes += box_count

    # --------------------------------------------------------
    # Analyze source groups
    # --------------------------------------------------------

    group_rows = []

    mixed_class_groups = []
    empty_groups = []

    supporting_source_groups = 0
    monopole_source_groups = 0

    for source_group in sorted(groups):

        records = groups[source_group]

        frame_count = len(records)

        total_group_boxes = sum(
            record["box_count"]
            for record in records
        )

        group_class_ids = sorted(
            {
                class_id
                for record in records
                for class_id in record["class_ids"]
            }
        )

        group_class_names = [
            CLASS_NAMES.get(
                class_id,
                f"unknown_{class_id}",
            )
            for class_id in group_class_ids
        ]

        frame_names = [
            record["file_stem"]
            for record in records
        ]

        # Determine the semantic class of the source group.
        # We expect all frames from one source to have the same class.
        if len(group_class_ids) == 1:

            group_class_id = group_class_ids[0]

            if group_class_id == 0:
                supporting_source_groups += 1

            elif group_class_id == 1:
                monopole_source_groups += 1

        elif len(group_class_ids) == 0:

            group_class_id = ""
            empty_groups.append(source_group)

        else:

            group_class_id = "MIXED"
            mixed_class_groups.append(
                source_group
            )

        group_rows.append(
            {
                "source_group": source_group,
                "frame_count": frame_count,
                "box_count": total_group_boxes,
                "class_ids": "|".join(
                    str(x)
                    for x in group_class_ids
                ),
                "class_names": "|".join(
                    group_class_names
                ),
                "frames": "|".join(
                    frame_names
                ),
                "status": (
                    "mixed_classes"
                    if len(group_class_ids) > 1
                    else (
                        "empty"
                        if len(group_class_ids) == 0
                        else "valid"
                    )
                ),
            }
        )

    # --------------------------------------------------------
    # Exact duplicate groups across SOURCE groups
    # --------------------------------------------------------

    cross_source_exact_duplicates = []

    for hash_value, records in exact_hash_groups.items():

        source_groups = sorted(
            {
                record["source_group"]
                for record in records
            }
        )

        if len(source_groups) <= 1:
            continue

        duplicate_rows = {
            "exact_hash": hash_value,
            "source_groups": source_groups,
            "files": [
                record["file_stem"]
                for record in records
            ],
        }

        cross_source_exact_duplicates.append(
            duplicate_rows
        )

    # --------------------------------------------------------
    # Perceptual near-duplicate candidates
    # --------------------------------------------------------

    # Only compare images belonging to DIFFERENT source groups.
    metadata_list = list(
        image_metadata.values()
    )

    near_duplicate_candidates = []

    # Conservative threshold.
    # These are only REVIEW candidates.
    DHASH_THRESHOLD = 4

    for i in range(len(metadata_list)):

        first = metadata_list[i]

        for j in range(i + 1, len(metadata_list)):

            second = metadata_list[j]

            if (
                first["source_group"]
                == second["source_group"]
            ):
                continue

            distance = hamming_distance(
                first["dhash"],
                second["dhash"],
            )

            if distance <= DHASH_THRESHOLD:

                near_duplicate_candidates.append(
                    {
                        "file_1": first["file_stem"],
                        "file_2": second["file_stem"],
                        "source_group_1": first[
                            "source_group"
                        ],
                        "source_group_2": second[
                            "source_group"
                        ],
                        "dhash_distance": distance,
                        "class_1": "|".join(
                            first["class_names"]
                        ),
                        "class_2": "|".join(
                            second["class_names"]
                        ),
                    }
                )

    near_duplicate_candidates.sort(
        key=lambda row: row["dhash_distance"]
    )

    # --------------------------------------------------------
    # Write source group CSV
    # --------------------------------------------------------

    with GROUP_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "source_group",
            "frame_count",
            "box_count",
            "class_ids",
            "class_names",
            "frames",
            "status",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(group_rows)

    # --------------------------------------------------------
    # Write duplicate CSV
    # --------------------------------------------------------

    duplicate_csv_rows = []

    for row in cross_source_exact_duplicates:

        duplicate_csv_rows.append(
            {
                "type": "exact_duplicate",
                "file_1": (
                    row["files"][0]
                    if len(row["files"]) > 0
                    else ""
                ),
                "file_2": (
                    row["files"][1]
                    if len(row["files"]) > 1
                    else ""
                ),
                "source_group_1": (
                    row["source_groups"][0]
                    if len(row["source_groups"]) > 0
                    else ""
                ),
                "source_group_2": (
                    row["source_groups"][1]
                    if len(row["source_groups"]) > 1
                    else ""
                ),
                "distance": 0,
            }
        )

    for row in near_duplicate_candidates:

        duplicate_csv_rows.append(
            {
                "type": "near_duplicate_candidate",
                "file_1": row["file_1"],
                "file_2": row["file_2"],
                "source_group_1": row[
                    "source_group_1"
                ],
                "source_group_2": row[
                    "source_group_2"
                ],
                "distance": row[
                    "dhash_distance"
                ],
            }
        )

    with DUPLICATE_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "type",
            "file_1",
            "file_2",
            "source_group_1",
            "source_group_2",
            "distance",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            duplicate_csv_rows
        )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    json_report = {
        "summary": {
            "images": len(image_files),
            "source_groups": len(groups),
            "total_boxes": total_boxes,
            "supporting_source_groups": (
                supporting_source_groups
            ),
            "monopole_source_groups": (
                monopole_source_groups
            ),
            "mixed_class_groups": len(
                mixed_class_groups
            ),
            "empty_groups": len(
                empty_groups
            ),
            "cross_source_exact_duplicate_groups": len(
                cross_source_exact_duplicates
            ),
            "near_duplicate_candidates": len(
                near_duplicate_candidates
            ),
            "dhash_threshold": DHASH_THRESHOLD,
        },
        "mixed_class_groups": mixed_class_groups,
        "empty_groups": empty_groups,
        "source_groups": group_rows,
        "cross_source_exact_duplicates": (
            cross_source_exact_duplicates
        ),
        "near_duplicate_candidates": (
            near_duplicate_candidates
        ),
    }

    with GROUP_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            json_report,
            f,
            indent=2,
        )

    duplicate_json = {
        "cross_source_exact_duplicates": (
            cross_source_exact_duplicates
        ),
        "near_duplicate_candidates": (
            near_duplicate_candidates
        ),
    }

    with DUPLICATE_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            duplicate_json,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # Terminal output
    # --------------------------------------------------------

    print()
    print("DATASET COUNTS")
    print("-" * 72)

    print(
        f"Images                  : {len(image_files)}"
    )

    print(
        f"Source groups           : {len(groups)}"
    )

    print(
        f"Total boxes             : {total_boxes}"
    )

    print()
    print("SOURCE GROUP CLASS DISTRIBUTION")
    print("-" * 72)

    print(
        f"Supporting source groups : "
        f"{supporting_source_groups}"
    )

    print(
        f"Monopole source groups   : "
        f"{monopole_source_groups}"
    )

    print()
    print("GROUP CONSISTENCY")
    print("-" * 72)

    print(
        f"Mixed-class groups       : "
        f"{len(mixed_class_groups)}"
    )

    print(
        f"Empty groups             : "
        f"{len(empty_groups)}"
    )

    print()
    print("DUPLICATE ANALYSIS")
    print("-" * 72)

    print(
        f"Cross-source exact duplicate groups : "
        f"{len(cross_source_exact_duplicates)}"
    )

    print(
        f"Near-duplicate candidates            : "
        f"{len(near_duplicate_candidates)}"
    )

    if mixed_class_groups:
        print()
        print("MIXED CLASS GROUPS")
        print("-" * 72)

        for group in mixed_class_groups:
            print(f"  {group}")

    if empty_groups:
        print()
        print("EMPTY GROUPS")
        print("-" * 72)

        for group in empty_groups:
            print(f"  {group}")

    print()
    print("REPORTS")
    print("-" * 72)

    print(
        f"Source group CSV       : {GROUP_CSV}"
    )

    print(
        f"Source group JSON      : {GROUP_JSON}"
    )

    print(
        f"Duplicate CSV          : {DUPLICATE_CSV}"
    )

    print(
        f"Duplicate JSON         : {DUPLICATE_JSON}"
    )

    print()
    print("=" * 72)

    if (
        not mixed_class_groups
        and not empty_groups
    ):
        print(
            "SOURCE GROUP ANALYSIS: STRUCTURALLY CONSISTENT"
        )
    else:
        print(
            "SOURCE GROUP ANALYSIS: REVIEW REQUIRED"
        )

    print("=" * 72)


if __name__ == "__main__":
    main()