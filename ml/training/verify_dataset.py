from __future__ import annotations

import tempfile
from pathlib import Path

import yaml
from ultralytics import YOLO


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_YAML = (
    PROJECT_ROOT
    / "ml"
    / "configs"
    / "dataset.yaml"
)

DATA_ROOT = PROJECT_ROOT / "data" / "processed"

MODEL_NAME = "yolo11n.pt"


# ============================================================
# HELPERS
# ============================================================

def build_resolved_yaml() -> Path:
    """Copy dataset.yaml with an absolute dataset path.

    Ultralytics resolves a relative `path:` against the current working
    directory (and then against its own datasets folder), which breaks when
    the script is started from anywhere other than the project root.
    Writing a temporary copy with an absolute path keeps the read test
    independent of the current working directory.
    """

    config = yaml.safe_load(
        DATASET_YAML.read_text(encoding="utf-8")
    )

    config["path"] = str(DATA_ROOT)

    missing = [
        DATA_ROOT / config[split]
        for split in ("train", "val")
        if split in config
        and not (DATA_ROOT / config[split]).exists()
    ]

    if missing:
        missing_list = "\n".join(f"  - {item}" for item in missing)
        raise FileNotFoundError(
            "Dataset folders not found:\n"
            f"{missing_list}\n\n"
            "Regenerate the dataset split first:\n"
            "  python ml\\dataset\\create_dataset_split.py"
        )

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        prefix="towervision_dataset_",
        delete=False,
        encoding="utf-8",
    )

    with handle:
        yaml.safe_dump(config, handle, sort_keys=False)

    return Path(handle.name)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("TOWERVISION AI - YOLO DATASET READ TEST")
    print("=" * 72)

    if not DATASET_YAML.exists():
        raise FileNotFoundError(
            f"Dataset YAML not found:\n{DATASET_YAML}"
        )

    print()
    print(f"Dataset YAML : {DATASET_YAML}")
    print(f"Dataset root : {DATA_ROOT}")
    print(f"Test model   : {MODEL_NAME}")

    # Loading the model verifies that the installed
    # Ultralytics package can initialize the chosen model.
    model = YOLO(MODEL_NAME)

    print()
    print("MODEL LOAD")
    print("-" * 72)
    print("YOLO11n loaded successfully.")

    # Validate the dataset through Ultralytics.
    print()
    print("DATASET LOAD")
    print("-" * 72)

    resolved_yaml = build_resolved_yaml()

    try:
        results = model.val(
            data=str(resolved_yaml),
            split="val",
            imgsz=640,
            batch=1,
            workers=0,
            verbose=False,
        )
    finally:
        resolved_yaml.unlink(missing_ok=True)

    print()
    print("Ultralytics successfully loaded the dataset.")
    print(
        f"Validation images : "
        f"{len(results.box.image_ids)}"
        if hasattr(results.box, "image_ids")
        else "Validation images : loaded"
    )

    print()
    print("=" * 72)
    print("YOLO DATASET READ TEST: PASSED")
    print("=" * 72)


if __name__ == "__main__":
    main()
