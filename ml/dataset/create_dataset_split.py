from pathlib import Path
from collections import defaultdict, deque
import csv
import json
import math
import shutil


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

SOURCE_GROUP_CSV = (
    PROJECT_ROOT
    / "data"
    / "reports"
    / "source_group_analysis.csv"
)

DUPLICATE_CSV = (
    PROJECT_ROOT
    / "data"
    / "reports"
    / "cross_source_duplicate_analysis.csv"
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "reports"
)

SPLIT_CSV = (
    REPORT_DIR
    / "dataset_split.csv"
)

SPLIT_JSON = (
    REPORT_DIR
    / "dataset_split.json"
)

SUMMARY_CSV = (
    REPORT_DIR
    / "dataset_split_summary.csv"
)

SUMMARY_JSON = (
    REPORT_DIR
    / "dataset_split_summary.json"
)

CLASS_NAMES = {
    0: "supporting_tower",
    1: "monopole_tower",
}

SPLITS = [
    "train",
    "val",
    "test",
]

# Desired image distribution.
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Deterministic seed used only for tie-breaking.
SEED = 42


# ============================================================
# HELPERS
# ============================================================

def parse_class_name(value):
    value = (value or "").strip()

    if value == "supporting_tower":
        return "supporting_tower"

    if value == "monopole_tower":
        return "monopole_tower"

    raise ValueError(
        f"Unexpected class name: {value!r}"
    )


def load_source_groups():
    if not SOURCE_GROUP_CSV.exists():
        raise FileNotFoundError(
            f"Source-group report not found:\n{SOURCE_GROUP_CSV}"
        )

    groups = {}

    with SOURCE_GROUP_CSV.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            source_group = row["source_group"]

            class_name = parse_class_name(
                row["class_names"]
            )

            frame_count = int(
                row["frame_count"]
            )

            box_count = int(
                row["box_count"]
            )

            groups[source_group] = {
                "source_group": source_group,
                "frame_count": frame_count,
                "box_count": box_count,
                "class_name": class_name,
                "frames": (
                    row["frames"].split("|")
                    if row["frames"]
                    else []
                ),
            }

    return groups


def build_duplicate_graph(source_groups):
    """
    Build connected components from:
      - exact duplicate relationships
      - near-duplicate candidates

    All connected source groups are forced into the same split.
    """

    graph = {
        group: set()
        for group in source_groups
    }

    if not DUPLICATE_CSV.exists():
        raise FileNotFoundError(
            f"Duplicate report not found:\n{DUPLICATE_CSV}"
        )

    used_edges = 0

    with DUPLICATE_CSV.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            group_a = (
                row["source_group_1"]
                .strip()
            )

            group_b = (
                row["source_group_2"]
                .strip()
            )

            if not group_a or not group_b:
                continue

            if group_a not in source_groups:
                raise ValueError(
                    f"Duplicate report references unknown "
                    f"source group: {group_a}"
                )

            if group_b not in source_groups:
                raise ValueError(
                    f"Duplicate report references unknown "
                    f"source group: {group_b}"
                )

            if group_a == group_b:
                continue

            graph[group_a].add(group_b)
            graph[group_b].add(group_a)

            used_edges += 1

    # --------------------------------------------------------
    # Connected components
    # --------------------------------------------------------

    visited = set()
    components = []

    for start in sorted(graph):

        if start in visited:
            continue

        queue = deque([start])
        component = []

        visited.add(start)

        while queue:

            current = queue.popleft()

            component.append(current)

            for neighbor in sorted(
                graph[current]
            ):

                if neighbor in visited:
                    continue

                visited.add(neighbor)
                queue.append(neighbor)

        component.sort()
        components.append(component)

    components.sort(
        key=lambda component: component[0]
    )

    return graph, components, used_edges


def build_clusters(
    source_groups,
    components,
):
    clusters = []

    source_to_cluster = {}

    for cluster_index, component in enumerate(
        components,
        start=1,
    ):

        cluster_id = (
            f"CLUSTER_{cluster_index:03d}"
        )

        records = [
            source_groups[group]
            for group in component
        ]

        class_names = sorted(
            {
                record["class_name"]
                for record in records
            }
        )

        if len(class_names) != 1:
            raise ValueError(
                "Leakage cluster contains multiple classes: "
                f"{cluster_id} -> {class_names}"
            )

        frame_count = sum(
            record["frame_count"]
            for record in records
        )

        box_count = sum(
            record["box_count"]
            for record in records
        )

        clusters.append(
            {
                "cluster_id": cluster_id,
                "source_groups": component,
                "source_group_count": len(
                    component
                ),
                "frame_count": frame_count,
                "box_count": box_count,
                "class_name": class_names[0],
            }
        )

        for group in component:
            source_to_cluster[group] = cluster_id

    return clusters, source_to_cluster


def target_counts(total):
    """
    Calculate desired image counts for train/val/test.
    The train count gets the remainder so totals always equal
    the original total.
    """

    val_target = round(
        total * VAL_RATIO
    )

    test_target = round(
        total * TEST_RATIO
    )

    train_target = (
        total
        - val_target
        - test_target
    )

    return {
        "train": train_target,
        "val": val_target,
        "test": test_target,
    }


def assign_clusters_to_splits(
    clusters,
    class_name,
):
    """
    Deterministically assign clusters to train/val/test.

    The objective is to get as close as possible to the target
    IMAGE counts for that class while keeping every leakage
    cluster intact.

    Exact image counts are preferred when achievable.
    """

    class_clusters = [
        cluster
        for cluster in clusters
        if cluster["class_name"] == class_name
    ]

    total_frames = sum(
        cluster["frame_count"]
        for cluster in class_clusters
    )

    targets = target_counts(
        total_frames
    )

    # --------------------------------------------------------
    # Dynamic programming over val/test image counts.
    #
    # Train receives everything not assigned to val/test.
    # --------------------------------------------------------

    target_val = targets["val"]
    target_test = targets["test"]

    # State:
    # (val_frames, test_frames)
    #
    # Value:
    # list of (cluster_index, split)
    #
    # We keep one deterministic path per state.
    states = {
        (0, 0): []
    }

    for index, cluster in enumerate(
        class_clusters
    ):

        size = cluster["frame_count"]

        next_states = {}

        for (
            val_frames,
            test_frames,
        ), decisions in states.items():

            # ----------------------------
            # TRAIN
            # ----------------------------

            state = (
                val_frames,
                test_frames,
            )

            candidate = (
                decisions
                + [(index, "train")]
            )

            if state not in next_states:
                next_states[state] = candidate

            # ----------------------------
            # VAL
            # ----------------------------

            new_val = (
                val_frames + size
            )

            if new_val <= target_val:

                state = (
                    new_val,
                    test_frames,
                )

                candidate = (
                    decisions
                    + [(index, "val")]
                )

                if state not in next_states:
                    next_states[state] = candidate

            # ----------------------------
            # TEST
            # ----------------------------

            new_test = (
                test_frames + size
            )

            if new_test <= target_test:

                state = (
                    val_frames,
                    new_test,
                )

                candidate = (
                    decisions
                    + [(index, "test")]
                )

                if state not in next_states:
                    next_states[state] = candidate

        states = next_states

    # --------------------------------------------------------
    # Find the state closest to target.
    # --------------------------------------------------------

    def score(state):
        val_frames, test_frames = state

        val_error = abs(
            val_frames - target_val
        )

        test_error = abs(
            test_frames - target_test
        )

        train_frames = (
            total_frames
            - val_frames
            - test_frames
        )

        train_error = abs(
            train_frames
            - targets["train"]
        )

        return (
            val_error
            + test_error
            + train_error,
            val_error,
            test_error,
            train_error,
            val_frames,
            test_frames,
        )

    best_state = min(
        states.keys(),
        key=score,
    )

    best_decisions = states[
        best_state
    ]

    assignments = {}

    for (
        index,
        split,
    ) in best_decisions:

        cluster = class_clusters[index]

        assignments[
            cluster["cluster_id"]
        ] = split

    return assignments, targets, best_state


def copy_split_files(
    all_records,
    source_to_cluster,
    cluster_split,
):
    """
    Copy image/label pairs into:

    data/processed/
        images/train
        images/val
        images/test
        labels/train
        labels/val
        labels/test
    """

    # --------------------------------------------------------
    # Create directories
    # --------------------------------------------------------

    for split in SPLITS:

        (
            OUTPUT_ROOT
            / "images"
            / split
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            OUTPUT_ROOT
            / "labels"
            / split
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

    copied = []

    for record in all_records:

        stem = record["file_stem"]

        source_group = record[
            "source_group"
        ]

        cluster_id = source_to_cluster[
            source_group
        ]

        split = cluster_split[
            cluster_id
        ]

        source_image = (
            IMAGE_DIR
            / record["image_file"]
        )

        source_label = (
            LABEL_DIR
            / record["label_file"]
        )

        if not source_image.exists():
            raise FileNotFoundError(
                f"Image missing: {source_image}"
            )

        if not source_label.exists():
            raise FileNotFoundError(
                f"Label missing: {source_label}"
            )

        destination_image = (
            OUTPUT_ROOT
            / "images"
            / split
            / source_image.name
        )

        destination_label = (
            OUTPUT_ROOT
            / "labels"
            / split
            / source_label.name
        )

        shutil.copy2(
            source_image,
            destination_image,
        )

        shutil.copy2(
            source_label,
            destination_label,
        )

        copied.append(
            {
                "file_stem": stem,
                "image_file": source_image.name,
                "label_file": source_label.name,
                "source_group": source_group,
                "cluster_id": cluster_id,
                "class_name": record[
                    "class_name"
                ],
                "split": split,
            }
        )

    return copied


def load_all_annotation_records(
    source_groups,
):
    records = []

    for source_group in sorted(
        source_groups
    ):

        group = source_groups[
            source_group
        ]

        for frame in group["frames"]:

            records.append(
                {
                    "file_stem": frame,
                    "image_file": (
                        f"{frame}.jpg"
                    ),
                    "label_file": (
                        f"{frame}.txt"
                    ),
                    "source_group": (
                        source_group
                    ),
                    "class_name": (
                        group["class_name"]
                    ),
                }
            )

    return records


def build_summary(copied_records):
    summary = defaultdict(
        lambda: {
            "images": 0,
            "supporting_tower": 0,
            "monopole_tower": 0,
            "source_groups": set(),
            "clusters": set(),
        }
    )

    for record in copied_records:

        split = record["split"]

        summary[split]["images"] += 1

        summary[split][
            record["class_name"]
        ] += 1

        summary[split][
            "source_groups"
        ].add(
            record["source_group"]
        )

        summary[split][
            "clusters"
        ].add(
            record["cluster_id"]
        )

    output = {}

    for split in SPLITS:

        output[split] = {
            "images": summary[split]["images"],
            "supporting_tower": summary[
                split
            ]["supporting_tower"],
            "monopole_tower": summary[
                split
            ]["monopole_tower"],
            "source_groups": len(
                summary[split][
                    "source_groups"
                ]
            ),
            "clusters": len(
                summary[split]["clusters"]
            ),
        }

    return output


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("TOWERVISION AI - LEAKAGE-SAFE DATASET SPLIT")
    print("=" * 72)

    # --------------------------------------------------------
    # Basic checks
    # --------------------------------------------------------

    if not IMAGE_DIR.exists():
        raise FileNotFoundError(
            f"Image directory not found:\n{IMAGE_DIR}"
        )

    if not LABEL_DIR.exists():
        raise FileNotFoundError(
            f"Label directory not found:\n{LABEL_DIR}"
        )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Prevent accidental overwrite
    # --------------------------------------------------------

    if OUTPUT_ROOT.exists():

        existing_files = [
            path
            for path in OUTPUT_ROOT.rglob("*")
            if path.is_file()
        ]

        if existing_files:
            raise RuntimeError(
                "data/processed already contains files.\n\n"
                "Delete the existing processed dataset first "
                "if you intend to regenerate the split."
            )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Load source information
    # --------------------------------------------------------

    source_groups = load_source_groups()

    if not source_groups:
        raise RuntimeError(
            "No source groups found."
        )

    print()
    print(
        f"Source groups loaded : "
        f"{len(source_groups)}"
    )

    # --------------------------------------------------------
    # Build leakage graph
    # --------------------------------------------------------

    (
        graph,
        components,
        edge_count,
    ) = build_duplicate_graph(
        source_groups
    )

    print(
        f"Duplicate/near-duplicate edges : "
        f"{edge_count}"
    )

    print(
        f"Leakage clusters               : "
        f"{len(components)}"
    )

    # --------------------------------------------------------
    # Build clusters
    # --------------------------------------------------------

    (
        clusters,
        source_to_cluster,
    ) = build_clusters(
        source_groups,
        components,
    )

    cluster_size_distribution = defaultdict(
        int
    )

    for cluster in clusters:
        cluster_size_distribution[
            cluster["frame_count"]
        ] += 1

    print()
    print("LEAKAGE CLUSTERS")
    print("-" * 72)

    for size in sorted(
        cluster_size_distribution
    ):
        print(
            f"Clusters with {size} frame(s) : "
            f"{cluster_size_distribution[size]}"
        )

    # --------------------------------------------------------
    # Assign each class independently
    # --------------------------------------------------------

    cluster_split = {}

    class_targets = {}
    class_actuals = {}

    for class_name in (
        "supporting_tower",
        "monopole_tower",
    ):

        (
            assignments,
            targets,
            best_state,
        ) = assign_clusters_to_splits(
            clusters,
            class_name,
        )

        cluster_split.update(
            assignments
        )

        class_targets[
            class_name
        ] = targets

        val_actual, test_actual = (
            best_state
        )

        total_class_frames = sum(
            cluster["frame_count"]
            for cluster in clusters
            if cluster["class_name"]
            == class_name
        )

        train_actual = (
            total_class_frames
            - val_actual
            - test_actual
        )

        class_actuals[
            class_name
        ] = {
            "train": train_actual,
            "val": val_actual,
            "test": test_actual,
            "total": total_class_frames,
        }

    # --------------------------------------------------------
    # Load annotation records
    # --------------------------------------------------------

    all_records = (
        load_all_annotation_records(
            source_groups
        )
    )

    if len(all_records) != 209:
        print()
        print(
            "WARNING:"
        )
        print(
            f"Expected 209 annotation frames "
            f"but found {len(all_records)}."
        )

    # --------------------------------------------------------
    # Copy files
    # --------------------------------------------------------

    print()
    print("COPYING DATASET")
    print("-" * 72)

    copied_records = copy_split_files(
        all_records,
        source_to_cluster,
        cluster_split,
    )

    print(
        f"Copied image/label pairs : "
        f"{len(copied_records)}"
    )

    # --------------------------------------------------------
    # Build summary
    # --------------------------------------------------------

    summary = build_summary(
        copied_records
    )

    # --------------------------------------------------------
    # Validate split integrity
    # --------------------------------------------------------

    seen_sources = {}
    seen_clusters = {}

    for record in copied_records:

        source_group = record[
            "source_group"
        ]

        cluster_id = record[
            "cluster_id"
        ]

        split = record["split"]

        previous_source_split = (
            seen_sources.get(source_group)
        )

        if (
            previous_source_split is not None
            and previous_source_split != split
        ):
            raise RuntimeError(
                f"Source leakage detected: "
                f"{source_group}"
            )

        seen_sources[
            source_group
        ] = split

        previous_cluster_split = (
            seen_clusters.get(cluster_id)
        )

        if (
            previous_cluster_split is not None
            and previous_cluster_split != split
        ):
            raise RuntimeError(
                f"Cluster leakage detected: "
                f"{cluster_id}"
            )

        seen_clusters[
            cluster_id
        ] = split

    # --------------------------------------------------------
    # Split CSV
    # --------------------------------------------------------

    with SPLIT_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "file_stem",
            "image_file",
            "label_file",
            "source_group",
            "cluster_id",
            "class_name",
            "split",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            copied_records
        )

    # --------------------------------------------------------
    # Summary CSV
    # --------------------------------------------------------

    summary_rows = []

    for split in SPLITS:

        row = {
            "split": split,
            "images": summary[split]["images"],
            "supporting_tower": summary[
                split
            ]["supporting_tower"],
            "monopole_tower": summary[
                split
            ]["monopole_tower"],
            "source_groups": summary[
                split
            ]["source_groups"],
            "clusters": summary[
                split
            ]["clusters"],
        }

        summary_rows.append(row)

    with SUMMARY_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "split",
            "images",
            "supporting_tower",
            "monopole_tower",
            "source_groups",
            "clusters",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            summary_rows
        )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    json_report = {
        "seed": SEED,
        "ratios": {
            "train": TRAIN_RATIO,
            "val": VAL_RATIO,
            "test": TEST_RATIO,
        },
        "source_groups": len(
            source_groups
        ),
        "duplicate_edges": edge_count,
        "leakage_clusters": len(
            clusters
        ),
        "class_targets": class_targets,
        "class_actuals": class_actuals,
        "split_summary": summary,
        "files": copied_records,
    }

    with SPLIT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            json_report,
            f,
            indent=2,
        )

    summary_json = {
        "ratios": {
            "train": TRAIN_RATIO,
            "val": VAL_RATIO,
            "test": TEST_RATIO,
        },
        "source_groups": len(
            source_groups
        ),
        "duplicate_edges": edge_count,
        "leakage_clusters": len(
            clusters
        ),
        "class_targets": class_targets,
        "class_actuals": class_actuals,
        "split_summary": summary,
    }

    with SUMMARY_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            summary_json,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # Terminal summary
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("FINAL DATASET SPLIT")
    print("=" * 72)

    print()
    print("OVERALL")
    print("-" * 72)

    total_images = len(
        copied_records
    )

    print(
        f"Total images       : {total_images}"
    )

    print(
        f"Source groups      : "
        f"{len(source_groups)}"
    )

    print(
        f"Leakage clusters   : "
        f"{len(clusters)}"
    )

    print()
    print("SPLIT DISTRIBUTION")
    print("-" * 72)

    for split in SPLITS:

        images = summary[split][
            "images"
        ]

        percentage = (
            images / total_images * 100.0
            if total_images
            else 0.0
        )

        print(
            f"{split:5s} : "
            f"{images:3d} images "
            f"({percentage:5.1f}%) | "
            f"supporting={summary[split]['supporting_tower']:3d} | "
            f"monopole={summary[split]['monopole_tower']:2d} | "
            f"groups={summary[split]['source_groups']:3d}"
        )

    print()
    print("OUTPUT")
    print("-" * 72)

    print(
        f"Images : "
        f"{OUTPUT_ROOT / 'images'}"
    )

    print(
        f"Labels : "
        f"{OUTPUT_ROOT / 'labels'}"
    )

    print(
        f"Split report : "
        f"{SPLIT_CSV}"
    )

    print(
        f"Summary CSV  : "
        f"{SUMMARY_CSV}"
    )

    print(
        f"Summary JSON : "
        f"{SUMMARY_JSON}"
    )

    print()
    print("=" * 72)
    print("DATASET SPLIT CREATED")
    print("=" * 72)


if __name__ == "__main__":
    main()