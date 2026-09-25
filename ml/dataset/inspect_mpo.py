from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError


# ============================================================
# TowerVision AI
# Phase 1 - MPO Frame Investigation
# ============================================================
#
# Purpose:
#   Investigate multi-frame MPO images before deciding how they
#   should be converted or incorporated into the training data.
#
# Input:
#   data/raw/
#
# Outputs:
#   data/reports/mpo_frame_analysis.csv
#   data/reports/mpo_frame_analysis.json
#
#   data/interim/
#       mpo_frame_1_contact_sheet.jpg
#       mpo_frame_2_contact_sheet.jpg
#
# Important:
#   This script NEVER modifies the raw dataset.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"

MPO_FORMAT = "MPO"

THUMBNAIL_WIDTH = 320
THUMBNAIL_HEIGHT = 240

CONTACT_COLUMNS = 5

BACKGROUND = (245, 245, 245)
TEXT_COLOR = (20, 20, 20)
BORDER_COLOR = (180, 180, 180)


def calculate_pixel_hash(image: Image.Image) -> str:
    """
    Create a deterministic hash from normalized RGB pixels.

    This lets us compare frames based on actual image content
    rather than container/file metadata.
    """
    normalized = image.convert("RGB").resize(
        (256, 256),
        Image.Resampling.LANCZOS,
    )

    pixel_bytes = np.asarray(
        normalized,
        dtype=np.uint8,
    ).tobytes()

    return hashlib.sha256(pixel_bytes).hexdigest()


def calculate_frame_similarity(
    image_a: Image.Image,
    image_b: Image.Image,
) -> float:
    """
    Calculate a simple normalized pixel similarity between two
    frames.

    The result is between 0 and 1:

        1.0 -> visually identical after normalization
        0.0 -> maximally different

    This is an investigation metric, not a machine-learning
    quality score.
    """
    a = np.asarray(
        image_a.convert("RGB").resize(
            (256, 256),
            Image.Resampling.LANCZOS,
        ),
        dtype=np.float32,
    )

    b = np.asarray(
        image_b.convert("RGB").resize(
            (256, 256),
            Image.Resampling.LANCZOS,
        ),
        dtype=np.float32,
    )

    mean_absolute_difference = np.mean(
        np.abs(a - b)
    )

    similarity = 1.0 - (
        mean_absolute_difference / 255.0
    )

    return round(
        float(np.clip(similarity, 0.0, 1.0)),
        6,
    )


def find_mpo_files() -> list[Path]:
    """
    Find raw files that Pillow identifies as MPO.

    File extension is not used as the primary test because the
    organizer's files may use .JPG while internally containing
    MPO data.
    """
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw dataset directory does not exist:\n{RAW_DIR}"
        )

    mpo_files: list[Path] = []

    for file_path in sorted(
        path
        for path in RAW_DIR.rglob("*")
        if path.is_file()
    ):
        try:
            with Image.open(file_path) as image:
                if image.format == MPO_FORMAT:
                    mpo_files.append(file_path)
        except Exception:
            continue

    return mpo_files


def inspect_mpo_file(
    file_path: Path,
) -> dict[str, Any]:
    """
    Inspect every frame of a single MPO image.
    """
    record: dict[str, Any] = {
        "file_name": file_path.name,
        "relative_path": str(
            file_path.relative_to(PROJECT_ROOT)
        ),
        "frame_count": None,
        "base_width": None,
        "base_height": None,
        "base_mode": None,
        "frame_dimensions": None,
        "frame_modes": None,
        "unique_frame_hashes": None,
        "identical_frame_pairs": 0,
        "frame_pair_similarities": None,
        "min_frame_similarity": None,
        "max_frame_similarity": None,
        "mean_frame_similarity": None,
        "status": "valid",
        "error": "",
    }

    try:
        with Image.open(file_path) as image:
            frame_count = getattr(
                image,
                "n_frames",
                1,
            )

            record["frame_count"] = int(frame_count)
            record["base_width"] = int(image.width)
            record["base_height"] = int(image.height)
            record["base_mode"] = image.mode

            frame_dimensions: list[list[int]] = []
            frame_modes: list[str] = []
            frame_hashes: list[str] = []
            frames: list[Image.Image] = []

            for frame_index in range(frame_count):
                image.seek(frame_index)

                frame = image.copy()

                frame_dimensions.append(
                    [
                        int(frame.width),
                        int(frame.height),
                    ]
                )

                frame_modes.append(frame.mode)

                frame_hashes.append(
                    calculate_pixel_hash(frame)
                )

                frames.append(frame)

            record["frame_dimensions"] = (
                frame_dimensions
            )

            record["frame_modes"] = frame_modes

            record["unique_frame_hashes"] = len(
                set(frame_hashes)
            )

            identical_pairs = 0
            similarities: list[float] = []

            for first_index in range(frame_count):
                for second_index in range(
                    first_index + 1,
                    frame_count,
                ):
                    similarity = calculate_frame_similarity(
                        frames[first_index],
                        frames[second_index],
                    )

                    similarities.append(
                        similarity
                    )

                    if (
                        frame_hashes[first_index]
                        == frame_hashes[second_index]
                    ):
                        identical_pairs += 1

            record[
                "identical_frame_pairs"
            ] = identical_pairs

            record[
                "frame_pair_similarities"
            ] = similarities

            if similarities:
                record[
                    "min_frame_similarity"
                ] = min(similarities)

                record[
                    "max_frame_similarity"
                ] = max(similarities)

                record[
                    "mean_frame_similarity"
                ] = round(
                    sum(similarities)
                    / len(similarities),
                    6,
                )

            for frame in frames:
                frame.close()

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as exc:
        record["status"] = "unreadable"
        record["error"] = str(exc)

    except Exception as exc:
        record["status"] = "inspection_error"
        record["error"] = (
            f"{type(exc).__name__}: {exc}"
        )

    return record


def load_frame(
    file_path: Path,
    frame_index: int,
) -> Image.Image | None:
    """
    Load one MPO frame as an independent RGB image.
    """
    try:
        image = Image.open(file_path)
        image.seek(frame_index)

        frame = image.convert("RGB").copy()

        image.close()

        return frame

    except Exception:
        return None


def create_contact_sheet(
    mpo_files: list[Path],
    frame_index: int,
    output_path: Path,
) -> None:
    """
    Create a contact sheet for one frame index across all MPO
    images.

    Each thumbnail contains:
      - file name
      - frame number
      - image preview
    """
    if not mpo_files:
        return

    cell_width = THUMBNAIL_WIDTH
    cell_height = THUMBNAIL_HEIGHT + 48

    rows = math.ceil(
        len(mpo_files) / CONTACT_COLUMNS
    )

    sheet_width = (
        CONTACT_COLUMNS * cell_width
    )

    sheet_height = (
        rows * cell_height
    )

    sheet = Image.new(
        "RGB",
        (sheet_width, sheet_height),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for index, file_path in enumerate(
        mpo_files
    ):
        row = index // CONTACT_COLUMNS
        column = index % CONTACT_COLUMNS

        x = column * cell_width
        y = row * cell_height

        frame = load_frame(
            file_path,
            frame_index,
        )

        if frame is None:
            draw.rectangle(
                [
                    x + 4,
                    y + 4,
                    x + cell_width - 4,
                    y + THUMBNAIL_HEIGHT - 4,
                ],
                outline=BORDER_COLOR,
                width=2,
            )

            draw.text(
                (
                    x + 10,
                    y + 15,
                ),
                "FRAME UNAVAILABLE",
                fill=TEXT_COLOR,
                font=font,
            )

        else:
            frame.thumbnail(
                (
                    THUMBNAIL_WIDTH - 12,
                    THUMBNAIL_HEIGHT - 12,
                ),
                Image.Resampling.LANCZOS,
            )

            image_x = x + (
                cell_width - frame.width
            ) // 2

            image_y = y + (
                THUMBNAIL_HEIGHT - frame.height
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
                    x + 4,
                    y + 4,
                    x + cell_width - 4,
                    y + THUMBNAIL_HEIGHT - 4,
                ],
                outline=BORDER_COLOR,
                width=1,
            )

            frame.close()

        label = (
            f"{file_path.name[:32]}\n"
            f"Frame {frame_index + 1}"
        )

        draw.text(
            (
                x + 8,
                y + THUMBNAIL_HEIGHT + 6,
            ),
            label,
            fill=TEXT_COLOR,
            font=font,
        )

    sheet.save(
        output_path,
        quality=92,
    )

    sheet.close()


def build_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build a summary of the MPO investigation.
    """
    valid_records = [
        record
        for record in records
        if record["status"] == "valid"
    ]

    frame_counts: dict[str, int] = {}

    for record in valid_records:
        frame_count = str(
            record["frame_count"]
        )

        frame_counts[frame_count] = (
            frame_counts.get(frame_count, 0) + 1
        )

    mean_similarities = [
        record["mean_frame_similarity"]
        for record in valid_records
        if record["mean_frame_similarity"]
        is not None
    ]

    return {
        "total_mpo_files": len(records),
        "valid_mpo_files": len(valid_records),
        "failed_mpo_files": (
            len(records) - len(valid_records)
        ),
        "frame_count_distribution": frame_counts,
        "average_frame_similarity": (
            round(
                sum(mean_similarities)
                / len(mean_similarities),
                6,
            )
            if mean_similarities
            else None
        ),
        "all_frames_identical_count": sum(
            1
            for record in valid_records
            if (
                record["frame_count"] == 2
                and record["identical_frame_pairs"] > 0
            )
        ),
    }


def save_reports(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """
    Save CSV and JSON reports.
    """
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    INTERIM_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = pd.DataFrame(records)

    csv_path = (
        REPORT_DIR
        / "mpo_frame_analysis.csv"
    )

    json_path = (
        REPORT_DIR
        / "mpo_frame_analysis.json"
    )

    dataframe.to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    payload = {
        "summary": summary,
        "records": records,
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
    print(f"CSV report : {csv_path}")
    print(f"JSON report: {json_path}")


def print_report(
    summary: dict[str, Any],
) -> None:
    """
    Print the investigation summary.
    """
    print()
    print("=" * 72)
    print("TOWERVISION AI - MPO FRAME INVESTIGATION")
    print("=" * 72)

    print(
        f"Total MPO files       : "
        f"{summary['total_mpo_files']}"
    )

    print(
        f"Valid MPO files       : "
        f"{summary['valid_mpo_files']}"
    )

    print(
        f"Failed MPO files      : "
        f"{summary['failed_mpo_files']}"
    )

    print()
    print("FRAME COUNT DISTRIBUTION")
    print("-" * 72)

    if summary["frame_count_distribution"]:
        for frame_count, count in sorted(
            summary["frame_count_distribution"].items(),
            key=lambda item: int(item[0]),
        ):
            print(
                f"{frame_count} frame(s)          : "
                f"{count}"
            )
    else:
        print("No valid MPO images found.")

    print()
    print("FRAME SIMILARITY")
    print("-" * 72)

    print(
        "Average pair similarity : "
        f"{summary['average_frame_similarity']}"
    )

    print(
        "2-frame files with "
        "identical frames      : "
        f"{summary['all_frames_identical_count']}"
    )

    print()
    print("=" * 72)
    print("MPO INVESTIGATION COMPLETE")
    print("=" * 72)
    print()


def main() -> None:
    """
    Main entry point.
    """
    print()
    print("Starting MPO investigation...")
    print(f"Scanning: {RAW_DIR}")
    print()

    mpo_files = find_mpo_files()

    print(
        f"Found {len(mpo_files)} MPO images."
    )

    records = []

    for index, file_path in enumerate(
        mpo_files,
        start=1,
    ):
        print(
            f"[{index:03d}/{len(mpo_files):03d}] "
            f"{file_path.name}"
        )

        records.append(
            inspect_mpo_file(file_path)
        )

    summary = build_summary(records)

    save_reports(
        records=records,
        summary=summary,
    )

    INTERIM_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    create_contact_sheet(
        mpo_files=mpo_files,
        frame_index=0,
        output_path=(
            INTERIM_DIR
            / "mpo_frame_1_contact_sheet.jpg"
        ),
    )

    create_contact_sheet(
        mpo_files=mpo_files,
        frame_index=1,
        output_path=(
            INTERIM_DIR
            / "mpo_frame_2_contact_sheet.jpg"
        ),
    )

    print_report(summary)

    print(
        "Contact sheet 1 : "
        f"{INTERIM_DIR / 'mpo_frame_1_contact_sheet.jpg'}"
    )

    print(
        "Contact sheet 2 : "
        f"{INTERIM_DIR / 'mpo_frame_2_contact_sheet.jpg'}"
    )

    print()


if __name__ == "__main__":
    main()