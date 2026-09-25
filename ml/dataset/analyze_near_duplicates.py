from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REPORT_DIR = DATA_DIR / "reports"
INTERIM_DIR = DATA_DIR / "interim"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

RESIZE_WIDTH = 256
RESIZE_HEIGHT = 256

# Candidate threshold — requires human review, not auto-delete.
PHASH_HAMMING_THRESHOLD = 10

CONTACT_SHEET_COLUMNS = 3
THUMBNAIL_WIDTH = 360
THUMBNAIL_HEIGHT = 260

BACKGROUND = (245, 245, 245)
TEXT_COLOR = (20, 20, 20)
BORDER_COLOR = (170, 170, 170)


def find_images() -> list[Path]:
    """
    Find every source image in data/raw.
    """
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw data directory does not exist:\n{RAW_DIR}"
        )

    return sorted(
        path
        for path in RAW_DIR.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
        )
    )


def load_image(
    path: Path,
) -> np.ndarray:
    """
    Load an image as a grayscale OpenCV array.
    """
    image = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE,
    )

    if image is None:
        raise ValueError(
            f"Could not decode image: {path.name}"
        )

    return image


def resize_for_comparison(
    image: np.ndarray,
) -> np.ndarray:
    """
    Resize an image to a common comparison size.
    """
    return cv2.resize(
        image,
        (RESIZE_WIDTH, RESIZE_HEIGHT),
        interpolation=cv2.INTER_AREA,
    )


def calculate_dhash(
    image: np.ndarray,
) -> str:
    """
    Calculate a difference hash (dHash).

    dHash captures local horizontal brightness changes and is
    useful for identifying visually similar images.
    """
    resized = cv2.resize(
        image,
        (65, 64),
        interpolation=cv2.INTER_AREA,
    )

    difference = resized[:, 1:] > resized[:, :-1]

    bits = "".join(
        "1" if value else "0"
        for value in difference.flatten()
    )

    hex_length = len(bits) // 4

    return "".join(
        f"{int(bits[i:i + 4], 2):x}"
        for i in range(
            0,
            hex_length * 4,
            4,
        )
    )


def hamming_distance(
    hash_a: str,
    hash_b: str,
) -> int:
    """
    Calculate the Hamming distance between two hexadecimal
    dHashes.
    """
    binary_a = bin(
        int(hash_a, 16)
    )[2:].zfill(
        len(hash_a) * 4
    )

    binary_b = bin(
        int(hash_b, 16)
    )[2:].zfill(
        len(hash_b) * 4
    )

    return sum(
        bit_a != bit_b
        for bit_a, bit_b in zip(
            binary_a,
            binary_b,
        )
    )


def calculate_ssim_like_similarity(
    image_a: np.ndarray,
    image_b: np.ndarray,
) -> float:
    """
    Simple normalized pixel similarity (secondary signal, not formal SSIM).
    """
    a = resize_for_comparison(
        image_a
    ).astype(
        np.float32
    )

    b = resize_for_comparison(
        image_b
    ).astype(
        np.float32
    )

    mae = float(
        np.mean(
            np.abs(a - b)
        )
    )

    similarity = 1.0 - (
        mae / 255.0
    )

    return float(
        np.clip(
            similarity,
            0.0,
            1.0,
        )
    )


def load_catalog() -> pd.DataFrame | None:
    """
    Load the existing master catalog if available.
    """
    catalog_path = (
        REPORT_DIR / "image_catalog.csv"
    )

    if not catalog_path.exists():
        return None

    dataframe = pd.read_csv(
        catalog_path
    )

    required_columns = {
        "source_group_id",
        "source_file_name",
        "frame_index",
        "source_format",
        "frame_id",
        "status",
    }

    if not required_columns.issubset(
        dataframe.columns
    ):
        raise ValueError(
            "image_catalog.csv is missing required columns."
        )

    return dataframe


def calculate_image_records(
    image_paths: list[Path],
) -> list[dict[str, Any]]:
    """
    Decode every frame represented by the master catalog.

    For MPO files, frame index is taken from image_catalog.csv.
    For normal images, frame index is zero.
    """
    catalog = load_catalog()

    records: list[dict[str, Any]] = []

    if catalog is None:
        raise FileNotFoundError(
            "image_catalog.csv was not found. "
            "Run build_image_catalog.py first."
        )

    path_lookup = {
        str(
            PROJECT_ROOT
            / row["source_relative_path"]
        ): row
        for _, row in catalog.iterrows()
        if row["status"] == "valid"
    }

    for image_path in image_paths:
        relative_key = str(image_path.resolve())

        matching_rows = [
            row
            for key, row in path_lookup.items()
            if str(Path(key).resolve())
            == relative_key
        ]

        if not matching_rows:
            continue

        with cv2.imdecode(
            np.fromfile(
                str(image_path),
                dtype=np.uint8,
            ),
            cv2.IMREAD_GRAYSCALE,
        ) as _:
            pass


def decode_frame(
    path: Path,
    frame_index: int,
) -> np.ndarray:
    """
    Decode a particular frame.

    Pillow is used because OpenCV does not directly expose MPO
    frame navigation.
    """
    from PIL import Image

    with Image.open(path) as image:
        image.seek(frame_index)

        frame = image.convert(
            "L"
        ).copy()

    return np.asarray(
        frame,
        dtype=np.uint8,
    )


def create_frame_inventory() -> list[dict[str, Any]]:
    """
    Build an image/frame inventory from image_catalog.csv.
    """
    catalog = load_catalog()

    if catalog is None:
        raise FileNotFoundError(
            "image_catalog.csv not found."
        )

    valid_catalog = catalog[
        catalog["status"] == "valid"
    ].copy()

    records: list[dict[str, Any]] = []

    total = len(valid_catalog)

    for index, (_, row) in enumerate(
        valid_catalog.iterrows(),
        start=1,
    ):
        path = (
            PROJECT_ROOT
            / row["source_relative_path"]
        )

        frame_index = int(
            row["frame_index"]
        )

        print(
            f"[{index:03d}/{total:03d}] "
            f"{row['frame_id']}"
        )

        image = decode_frame(
            path,
            frame_index,
        )

        normalized = resize_for_comparison(
            image
        )

        dhash = calculate_dhash(
            image
        )

        records.append(
            {
                "frame_id": row["frame_id"],
                "source_group_id": row[
                    "source_group_id"
                ],
                "source_file_name": row[
                    "source_file_name"
                ],
                "frame_index": frame_index,
                "source_format": row[
                    "source_format"
                ],
                "width": int(
                    row["width"]
                ),
                "height": int(
                    row["height"]
                ),
                "dhash": dhash,
                "mean_brightness": round(
                    float(
                        np.mean(
                            normalized
                        )
                    ),
                    4,
                ),
            }
        )

    return records


def find_candidate_pairs(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Compare every frame against every other frame.

    Pairs from the same source group are still reported, but the
    primary interest is cross-source similarity.

    Since the dataset contains only 209 frames, an O(n^2)
    comparison is perfectly reasonable.
    """
    candidates: list[dict[str, Any]] = []

    image_cache: dict[
        str,
        np.ndarray,
    ] = {}

    for record in records:
        path = (
            PROJECT_ROOT
            / record["source_file_name"]
        )

        # Resolve path using source metadata from catalog.
        catalog = load_catalog()

        if catalog is None:
            continue

        rows = catalog[
            catalog["frame_id"]
            == record["frame_id"]
        ]

        if rows.empty:
            continue

        relative_path = rows.iloc[0][
            "source_relative_path"
        ]

        actual_path = (
            PROJECT_ROOT
            / relative_path
        )

        image_cache[
            record["frame_id"]
        ] = decode_frame(
            actual_path,
            int(
                record["frame_index"]
            ),
        )

    total = len(records)

    for i in range(total):
        record_a = records[i]

        for j in range(
            i + 1,
            total,
        ):
            record_b = records[j]

            if (
                record_a["frame_id"]
                == record_b["frame_id"]
            ):
                continue

            distance = hamming_distance(
                record_a["dhash"],
                record_b["dhash"],
            )

            if distance > PHASH_HAMMING_THRESHOLD:
                continue

            image_a = image_cache.get(
                record_a["frame_id"]
            )

            image_b = image_cache.get(
                record_b["frame_id"]
            )

            if image_a is None or image_b is None:
                continue

            similarity = (
                calculate_ssim_like_similarity(
                    image_a,
                    image_b,
                )
            )

            candidates.append(
                {
                    "frame_a": record_a[
                        "frame_id"
                    ],
                    "frame_b": record_b[
                        "frame_id"
                    ],
                    "source_group_a": record_a[
                        "source_group_id"
                    ],
                    "source_group_b": record_b[
                        "source_group_id"
                    ],
                    "same_source_group": (
                        record_a[
                            "source_group_id"
                        ]
                        == record_b[
                            "source_group_id"
                        ]
                    ),
                    "dhash_distance": distance,
                    "pixel_similarity": round(
                        similarity,
                        6,
                    ),
                    "relationship": (
                        "same_source_pair"
                        if (
                            record_a[
                                "source_group_id"
                            ]
                            == record_b[
                                "source_group_id"
                            ]
                        )
                        else "cross_source_candidate"
                    ),
                }
            )

    return candidates


def build_summary(
    records: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build summary statistics.
    """
    cross_source = [
        candidate
        for candidate in candidates
        if not candidate[
            "same_source_group"
        ]
    ]

    same_source = [
        candidate
        for candidate in candidates
        if candidate[
            "same_source_group"
        ]
    ]

    return {
        "total_frames": len(records),
        "candidate_pairs_total": len(
            candidates
        ),
        "same_source_candidates": len(
            same_source
        ),
        "cross_source_candidates": len(
            cross_source
        ),
        "thresholds": {
            "dhash_hamming_distance": (
                PHASH_HAMMING_THRESHOLD
            ),
        },
    }


def create_candidate_contact_sheet(
    candidates: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """
    Contact sheet for cross-source near-duplicate candidates (human review).
    """
    from PIL import Image, ImageDraw, ImageFont

    cross_source = [
        candidate
        for candidate in candidates
        if not candidate[
            "same_source_group"
        ]
    ]

    if not cross_source:
        return

    catalog = load_catalog()

    if catalog is None:
        return

    lookup = {
        row["frame_id"]: row
        for _, row in catalog.iterrows()
    }

    rows = len(cross_source)

    cell_width = THUMBNAIL_WIDTH
    cell_height = THUMBNAIL_HEIGHT + 90

    sheet = Image.new(
        "RGB",
        (
            cell_width * CONTACT_SHEET_COLUMNS,
            cell_height
            * (
                (
                    rows
                    + CONTACT_SHEET_COLUMNS
                    - 1
                )
                // CONTACT_SHEET_COLUMNS
            ),
        ),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for index, candidate in enumerate(
        cross_source
    ):
        row_number = (
            index
            // CONTACT_SHEET_COLUMNS
        )

        column = (
            index
            % CONTACT_SHEET_COLUMNS
        )

        x = column * cell_width
        y = row_number * cell_height

        frame_a_id = candidate[
            "frame_a"
        ]

        frame_b_id = candidate[
            "frame_b"
        ]

        for offset, frame_id in enumerate(
            [
                frame_a_id,
                frame_b_id,
            ]
        ):
            catalog_row = lookup.get(
                frame_id
            )

            if catalog_row is None:
                continue

            path = (
                PROJECT_ROOT
                / catalog_row[
                    "source_relative_path"
                ]
            )

            try:
                frame = Image.open(
                    path
                )

                frame.seek(
                    int(
                        catalog_row[
                            "frame_index"
                        ]
                    )
                )

                frame = frame.convert(
                    "RGB"
                )

                frame.thumbnail(
                    (
                        THUMBNAIL_WIDTH // 2
                        - 8,
                        THUMBNAIL_HEIGHT - 8,
                    ),
                    Image.Resampling.LANCZOS,
                )

                box_width = (
                    THUMBNAIL_WIDTH // 2
                )

                paste_x = (
                    x
                    + offset * box_width
                    + (
                        box_width
                        - frame.width
                    )
                    // 2
                )

                paste_y = (
                    y
                    + (
                        THUMBNAIL_HEIGHT
                        - frame.height
                    )
                    // 2
                )

                sheet.paste(
                    frame,
                    (
                        paste_x,
                        paste_y,
                    ),
                )

                frame.close()

            except Exception:
                continue

        label = (
            f"{frame_a_id}  ↔  {frame_b_id}\n"
            f"dHash distance: "
            f"{candidate['dhash_distance']}\n"
            f"Pixel similarity: "
            f"{candidate['pixel_similarity']}"
        )

        draw.text(
            (
                x + 6,
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


def save_outputs(
    records: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
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

    frame_dataframe = pd.DataFrame(
        records
    )

    candidate_dataframe = pd.DataFrame(
        candidates
    )

    frame_csv = (
        REPORT_DIR
        / "near_duplicate_frame_inventory.csv"
    )

    candidate_csv = (
        REPORT_DIR
        / "near_duplicate_candidates.csv"
    )

    json_path = (
        REPORT_DIR
        / "near_duplicate_analysis.json"
    )

    frame_dataframe.to_csv(
        frame_csv,
        index=False,
        encoding="utf-8",
    )

    candidate_dataframe.to_csv(
        candidate_csv,
        index=False,
        encoding="utf-8",
    )

    payload = {
        "summary": summary,
        "frames": records,
        "candidate_pairs": candidates,
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

    contact_sheet_path = (
        INTERIM_DIR
        / "near_duplicate_candidates.jpg"
    )

    create_candidate_contact_sheet(
        candidates=candidates,
        output_path=contact_sheet_path,
    )

    print()
    print(
        f"Frame inventory : {frame_csv}"
    )
    print(
        f"Candidate pairs : {candidate_csv}"
    )
    print(
        f"JSON report     : {json_path}"
    )
    print(
        f"Contact sheet   : {contact_sheet_path}"
    )


def main() -> None:
    """
    Main entry point.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - NEAR DUPLICATE ANALYSIS"
    )
    print("=" * 72)
    print()

    image_paths = find_images()

    print(
        f"Found {len(image_paths)} source image files."
    )

    print()
    print("Building frame inventory...")

    records = create_frame_inventory()

    print()
    print(
        f"Frame records created: {len(records)}"
    )

    print()
    print(
        "Comparing frames for near duplicates..."
    )

    candidates = find_candidate_pairs(
        records
    )

    summary = build_summary(
        records=records,
        candidates=candidates,
    )

    save_outputs(
        records=records,
        candidates=candidates,
        summary=summary,
    )

    print()
    print("SUMMARY")
    print("-" * 72)
    print(
        f"Frames analyzed        : "
        f"{summary['total_frames']}"
    )
    print(
        f"Candidate pairs        : "
        f"{summary['candidate_pairs_total']}"
    )
    print(
        f"Same-source candidates : "
        f"{summary['same_source_candidates']}"
    )
    print(
        f"Cross-source candidates: "
        f"{summary['cross_source_candidates']}"
    )

    print()
    print(
        "IMPORTANT:"
    )
    print(
        "Candidate near-duplicates require human review."
    )
    print(
        "No images have been deleted or modified."
    )

    print()
    print("=" * 72)
    print(
        "NEAR DUPLICATE ANALYSIS COMPLETE"
    )
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()