from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

import pandas as pd


# ============================================================
# TowerVision AI
# Phase 1 - Annotation Error Inspection
# ============================================================
#
# Purpose:
#   Inspect the exact annotation errors reported by
#   validate_annotations.py.
#
# Input:
#   data/reports/annotation_validation.csv
#
# Output:
#   data/reports/annotation_error_summary.csv
#
# This script DOES NOT modify any annotation or image.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "reports"
)

VALIDATION_REPORT = (
    REPORT_DIR
    / "annotation_validation.csv"
)

ERROR_SUMMARY_REPORT = (
    REPORT_DIR
    / "annotation_error_summary.csv"
)


def load_validation_report() -> pd.DataFrame:
    """
    Load the annotation validation report.
    """
    if not VALIDATION_REPORT.exists():
        raise FileNotFoundError(
            "annotation_validation.csv not found.\n"
            "Run validate_annotations.py first."
        )

    return pd.read_csv(
        VALIDATION_REPORT
    )


def parse_errors(
    error_text: str,
) -> list[str]:
    """
    Convert the stored error field into a list of individual
    annotation errors.
    """
    if (
        pd.isna(error_text)
        or not str(error_text).strip()
    ):
        return []

    text = str(
        error_text
    )

    # The validator stores errors using:
    # " | ".join(errors)
    return [
        item.strip()
        for item in text.split("|")
        if item.strip()
    ]


def normalize_error_name(
    error: str,
) -> str:
    """
    Remove the line number so identical error types can be
    grouped together.
    """
    if error.startswith(
        "line_"
    ):
        parts = error.split(
            ":",
            maxsplit=1,
        )

        if len(parts) == 2:
            return parts[1]

    return error


def build_error_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Count every unique validation error type.
    """
    counter: Counter[str] = Counter()

    for error_text in dataframe[
        "errors"
    ].fillna(""):
        errors = parse_errors(
            error_text
        )

        for error in errors:
            counter[
                normalize_error_name(
                    error
                )
            ] += 1

    rows = [
        {
            "error_type": error,
            "count": count,
        }
        for error, count in counter.most_common()
    ]

    return pd.DataFrame(
        rows
    )


def print_invalid_images(
    dataframe: pd.DataFrame,
) -> None:
    """
    Print every invalid annotation file with its errors.
    """
    invalid = dataframe[
        dataframe["status"]
        == "invalid"
    ].copy()

    print()
    print("=" * 72)
    print(
        "INVALID ANNOTATION FILES"
    )
    print("=" * 72)
    print()

    if invalid.empty:
        print(
            "No invalid annotation files found."
        )
        return

    for index, (_, row) in enumerate(
        invalid.iterrows(),
        start=1,
    ):
        print(
            f"[{index:02d}/{len(invalid):02d}] "
            f"{row['file_stem']}"
        )

        print(
            f"  Image : "
            f"{row['image_file']}"
        )

        print(
            f"  Label : "
            f"{row['label_file']}"
        )

        print(
            f"  Boxes : "
            f"{row['label_line_count']}"
        )

        print(
            f"  Error : "
            f"{row['errors']}"
        )

        print()


def print_error_summary(
    error_summary: pd.DataFrame,
) -> None:
    """
    Print aggregated error types.
    """
    print()
    print("=" * 72)
    print(
        "ANNOTATION ERROR TYPE SUMMARY"
    )
    print("=" * 72)
    print()

    if error_summary.empty:
        print(
            "No validation errors found."
        )
        return

    for _, row in (
        error_summary.iterrows()
    ):
        print(
            f"{row['error_type']:45} "
            f"{int(row['count'])}"
        )

    print()


def print_class_information(
    dataframe: pd.DataFrame,
) -> None:
    """
    Print class counts among valid parsed annotations.
    """
    supporting = int(
        dataframe[
            "supporting_tower_count"
        ].sum()
    )

    monopole = int(
        dataframe[
            "monopole_tower_count"
        ].sum()
    )

    print("=" * 72)
    print(
        "ANNOTATION CLASS COUNTS"
    )
    print("=" * 72)
    print()

    print(
        f"supporting_tower : {supporting}"
    )

    print(
        f"monopole_tower   : {monopole}"
    )

    total = (
        supporting
        + monopole
    )

    if total > 0:
        print()
        print(
            f"supporting_tower share : "
            f"{supporting / total * 100:.2f}%"
        )

        print(
            f"monopole_tower share   : "
            f"{monopole / total * 100:.2f}%"
        )

    print()


def save_error_summary(
    dataframe: pd.DataFrame,
) -> None:
    """
    Save aggregated error information.
    """
    ERROR_SUMMARY_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    error_summary = build_error_summary(
        dataframe
    )

    error_summary.to_csv(
        ERROR_SUMMARY_REPORT,
        index=False,
        encoding="utf-8",
    )

    print(
        f"Error summary CSV: "
        f"{ERROR_SUMMARY_REPORT}"
    )


def main() -> None:
    """
    Main entry point.
    """
    print()
    print("=" * 72)
    print(
        "TOWERVISION AI - ANNOTATION ERROR INSPECTION"
    )
    print("=" * 72)
    print()

    dataframe = load_validation_report()

    print(
        f"Validation records: "
        f"{len(dataframe)}"
    )

    invalid = dataframe[
        dataframe["status"]
        == "invalid"
    ]

    print(
        f"Invalid records  : "
        f"{len(invalid)}"
    )

    print_invalid_images(
        dataframe
    )

    error_summary = build_error_summary(
        dataframe
    )

    print_error_summary(
        error_summary
    )

    print_class_information(
        dataframe
    )

    save_error_summary(
        dataframe
    )

    print()
    print("=" * 72)
    print(
        "ANNOTATION ERROR INSPECTION COMPLETE"
    )
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()