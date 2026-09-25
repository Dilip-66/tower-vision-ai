from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image


# ============================================================
# TowerVision AI
# Phase 1 - Master Image Catalog
# ============================================================
#
# Purpose:
#   Create a canonical catalog of every source image and every
#   frame contained inside an MPO image.
#
# IMPORTANT:
#   This script does NOT modify the original data/raw files.
#   It only creates metadata and a visual-review contact sheet.
#
# Input:
#   data/raw/
#
# Outputs:
#   data/reports/image_catalog.csv
#   data/reports/image_catalog.json
#
#   data/interim/
#       image_catalog_contact_sheet.jpg
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

THUMBNAIL_SIZE = (300, 220)
COLUMNS = 4
TEXT_HEIGHT = 45

BACKGROUND = (245, 245, 245)
TEXT_COLOR = (25, 25, 25)
BORDER_COLOR = (170, 170, 170)


def calculate_sha256(
    file_path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """
    Calculate SHA-256 for an original source file.
    """
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def calculate_frame_hash(
    image: Image.Image,
) -> str:
    """
    Calculate a content hash for one decoded image frame.

    The image is normalized before hashing so the hash represents
    the frame's pixel content rather than its container metadata.
    """
    normalized = image.convert("RGB").resize(
        (256, 256),
        Image.Resampling.LANCZOS,
    )

    data = normalized.tobytes()

    return hashlib.sha256(data).hexdigest()


def classify_source_format(
    image: Image.Image,
) -> str:
    """
    Return the actual format reported by Pillow.
    """
    return str(image.format)


def determine_source_group_id(
    index: int,
) -> str:
    """
    Create a stable group identifier.

    Every frame from the same original source file receives the
    same group ID. This is critical for leakage-safe splitting.
    """
    return f"SOURCE_{index:04d}"


def inspect_source(
    file_path: Path,
    source_index: int,
) -> list[dict[str, Any]]:
    """
    Inspect one source image.

    For a normal image:
        one catalog row is created.

    For an MPO image:
        one row is created per frame.
    """
    source_group_id = determine_source_group_id(
        source_index
    )

    source_hash = calculate_sha256(file_path)

    records: list[dict[str, Any]] = []

    with Image.open(file_path) as image:
        actual_format = classify_source_format(image)

        frame_count = getattr(
            image,
            "n_frames",
            1,
        )

        for frame_index in range(frame_count):
            image.seek(frame_index)

            frame = image.copy()

            width = int(frame.width)
            height = int(frame.height)

            record = {
                "source_group_id": source_group_id,
                "source_file_name": file_path.name,
                "source_relative_path": str(
                    file_path.relative_to(PROJECT_ROOT)
                ),
                "source_extension": file_path.suffix.lower(),
                "source_format": actual_format,
                "source_sha256": source_hash,
                "frame_index": frame_index,
                "frame_id": (
                    f"{source_group_id}_FRAME_"
                    f"{frame_index:02d}"
                ),
                "frame_count": int(frame_count),
                "width": width,
                "height": height,
                "aspect_ratio": round(
                    width / height,
                    4,
                )
                if height > 0
                else None,
                "megapixels": round(
                    (width * height) / 1_000_000,
                    3,
                ),
                "frame_sha256": calculate_frame_hash(
                    frame
                ),
                "is_mpo": actual_format == "MPO",
                "status": "valid",
            }

            records.append(record)

            frame.close()

    return records


def find_source_images() -> list[Path]:
    """
    Find all supported images under data/raw.
    """
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw dataset directory does not exist:\n{RAW_DIR}"
        )

    return sorted(
        path
        for path in RAW_DIR.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    )


def build_catalog() -> list[dict[str, Any]]:
    """
    Build the complete image/frame catalog.
    """
    source_files = find_source_images()

    all_records: list[dict[str, Any]] = []

    total_sources = len(source_files)

    print(
        f"Found {total_sources} source image files."
    )

    for index, file_path in enumerate(
        source_files,
        start=1,
    ):
        print(
            f"[{index:03d}/{total_sources:03d}] "
            f"{file_path.name}"
        )

        try:
            records = inspect_source(
                file_path=file_path,
                source_index=index,
            )

            all_records.extend(records)

        except Exception as exc:
            all_records.append(
                {
                    "source_group_id": (
                        determine_source_group_id(index)
                    ),
                    "source_file_name": file_path.name,
                    "source_relative_path": str(
                        file_path.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                    "source_extension": (
                        file_path.suffix.lower()
                    ),
                    "source_format": None,
                    "source_sha256": (
                        calculate_sha256(file_path)
                    ),
                    "frame_index": None,
                    "frame_id": None,
                    "frame_count": None,
                    "width": None,
                    "height": None,
                    "aspect_ratio": None,
                    "megapixels": None,
                    "frame_sha256": None,
                    "is_mpo": None,
                    "status": (
                        f"error: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                }
            )

    return all_records


def build_summary(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Build summary statistics from the catalog.
    """
    valid = dataframe[
        dataframe["status"] == "valid"
    ].copy()

    source_count = (
        valid["source_group_id"]
        .nunique()
    )

    frame_count = len(valid)

    mpo_frame_count = int(
        valid["is_mpo"].fillna(False).sum()
    )

    normal_frame_count = (
        frame_count - mpo_frame_count
    )

    unique_source_hashes = (
        valid["source_sha256"]
        .nunique()
    )

    unique_frame_hashes = (
        valid["frame_sha256"]
        .nunique()
    )

    duplicate_frame_count = (
        frame_count
        - unique_frame_hashes
    )

    frame_distribution = (
        valid.groupby(
            "source_group_id"
        )["frame_count"]
        .first()
        .value_counts()
        .sort_index()
        .to_dict()
    )

    format_distribution = (
        valid["source_format"]
        .value_counts()
        .to_dict()
    )

    return {
        "source_images": int(source_count),
        "catalog_frames": int(frame_count),
        "mpo_frames": mpo_frame_count,
        "non_mpo_frames": int(
            normal_frame_count
        ),
        "unique_source_files": int(
            unique_source_hashes
        ),
        "unique_frame_hashes": int(
            unique_frame_hashes
        ),
        "duplicate_decoded_frames": int(
            duplicate_frame_count
        ),
        "source_frame_count_distribution": {
            str(key): int(value)
            for key, value
            in frame_distribution.items()
        },
        "format_distribution": {
            str(key): int(value)
            for key, value
            in format_distribution.items()
        },
    }


def save_reports(
    dataframe: pd.DataFrame,
    summary: dict[str, Any],
) -> None:
    """
    Save the image catalog as CSV and JSON.
    """
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        REPORT_DIR
        / "image_catalog.csv"
    )

    json_path = (
        REPORT_DIR
        / "image_catalog.json"
    )

    dataframe.to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    payload = {
        "summary": summary,
        "records": dataframe.to_dict(
            orient="records"
        ),
    }

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(
        f"CSV report : {csv_path}"
    )

    print(
        f"JSON report: {json_path}"
    )


def create_contact_sheet(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Create a visual catalog using representative thumbnails.

    For each source group, only frame 0 is shown. This prevents
    the 85 MPO pairs from flooding the contact sheet twice.

    The catalog itself still retains every frame.
    """
    valid = dataframe[
        dataframe["status"] == "valid"
    ].copy()

    representative = valid[
        valid["frame_index"] == 0
    ].reset_index(drop=True)

    if representative.empty:
        return

    cell_width = THUMBNAIL_SIZE[0]
    cell_height = (
        THUMBNAIL_SIZE[1]
        + TEXT_HEIGHT
    )

    rows = (
        len(representative)
        + COLUMNS
        - 1
    ) // COLUMNS

    sheet_width = COLUMNS * cell_width
    sheet_height = rows * cell_height

    sheet = Image.new(
        "RGB",
        (
            sheet_width,
            sheet_height,
        ),
        BACKGROUND,
    )

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    from PIL import ImageDraw

    draw = ImageDraw.Draw(sheet)

    for index, row in representative.iterrows():
        source_path = (
            PROJECT_ROOT
            / row["source_relative_path"]
        )

        try:
            with Image.open(source_path) as image:
                image.seek(0)

                frame = image.convert(
                    "RGB"
                ).copy()

            frame.thumbnail(
                THUMBNAIL_SIZE,
                Image.Resampling.LANCZOS,
            )

            column = index % COLUMNS
            row_number = index // COLUMNS

            x = column * cell_width
            y = row_number * cell_height

            image_x = x + (
                cell_width
                - frame.width
            ) // 2

            image_y = y + (
                THUMBNAIL_SIZE[1]
                - frame.height
            ) // 2

            sheet.paste(
                frame,
                (
                    image_x,
                    image_y,
                ),
            )

            draw.rectangle(
                [
                    x + 3,
                    y + 3,
                    x + cell_width - 3,
                    y + THUMBNAIL_SIZE[1] - 3,
                ],
                outline=BORDER_COLOR,
                width=1,
            )

            label = (
                f"{row['source_group_id']} | "
                f"{row['source_format']}\n"
                f"{row['source_file_name'][:34]}"
            )

            draw.text(
                (
                    x + 7,
                    y + THUMBNAIL_SIZE[1] + 5,
                ),
                label,
                fill=TEXT_COLOR,
                font=font,
            )

            frame.close()

        except Exception:
            continue

    sheet.save(
        output_path,
        quality=92,
    )

    sheet.close()


def main() -> None:
    """
    Main program entry point.
    """
    print()
    print("=" * 72)
    print("TOWERVISION AI - MASTER IMAGE CATALOG")
    print("=" * 72)
    print()

    records = build_catalog()

    dataframe = pd.DataFrame(records)

    summary = build_summary(dataframe)

    save_reports(
        dataframe=dataframe,
        summary=summary,
    )

    INTERIM_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    contact_sheet_path = (
        INTERIM_DIR
        / "image_catalog_contact_sheet.jpg"
    )

    create_contact_sheet(
        dataframe=dataframe,
        output_path=contact_sheet_path,
    )

    print()
    print("CATALOG SUMMARY")
    print("-" * 72)
    print(
        f"Source images          : "
        f"{summary['source_images']}"
    )
    print(
        f"Catalog frames         : "
        f"{summary['catalog_frames']}"
    )
    print(
        f"MPO frames             : "
        f"{summary['mpo_frames']}"
    )
    print(
        f"Non-MPO frames         : "
        f"{summary['non_mpo_frames']}"
    )
    print(
        f"Unique source hashes   : "
        f"{summary['unique_source_files']}"
    )
    print(
        f"Unique frame hashes    : "
        f"{summary['unique_frame_hashes']}"
    )
    print(
        f"Duplicate frames       : "
        f"{summary['duplicate_decoded_frames']}"
    )

    print()
    print("SOURCE FRAME DISTRIBUTION")
    print("-" * 72)

    for (
        frame_count,
        count,
    ) in summary[
        "source_frame_count_distribution"
    ].items():
        print(
            f"{frame_count} frame(s)          : "
            f"{count} source(s)"
        )

    print()
    print("FORMAT DISTRIBUTION")
    print("-" * 72)

    for (
        image_format,
        count,
    ) in summary[
        "format_distribution"
    ].items():
        print(
            f"{image_format:25} {count}"
        )

    print()
    print(
        f"Contact sheet : "
        f"{contact_sheet_path}"
    )

    print()
    print("=" * 72)
    print("MASTER IMAGE CATALOG COMPLETE")
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()