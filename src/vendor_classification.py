"""
VendorIQ - Vendor Performance Classification

Classifies vendors using rule-based business logic.

Input:
    data/processed/vendor_features.csv

Output:
    data/processed/vendor_classification.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# 1. Define paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vendor_features.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vendor_classification.csv"
)


# --------------------------------------------------
# 2. Load data
# --------------------------------------------------

def load_data():
    """Load the vendor feature dataset."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print("=" * 60)
    print("VENDORIQ - VENDOR PERFORMANCE CLASSIFICATION")
    print("=" * 60)

    print(f"Input file: {INPUT_FILE.name}")
    print(f"Dataset shape: {df.shape}")

    return df


# --------------------------------------------------
# 3. Validate input
# --------------------------------------------------

def validate_input(df):
    """Validate columns required for classification."""

    required_columns = [
        "VendorNumber",
        "VendorName",
        "GrossProfit",
        "GrossProfitMarginPercent",
        "TotalFreightCost",
        "TotalSalesRevenue",
        "FreightToRevenueRatio",
        "EstimatedProfitAfterFreight",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df["VendorNumber"].isna().any():
        raise ValueError("VendorNumber contains missing values.")

    if df["VendorNumber"].duplicated().any():
        raise ValueError("Duplicate vendors found.")

    if df[required_columns].isna().any().any():
        raise ValueError(
            "Missing values found in required classification columns."
        )

    print("\nInput validation passed.")


# --------------------------------------------------
# 4. Calculate classification thresholds
# --------------------------------------------------

def calculate_thresholds(df):
    """
    Calculate dataset-based thresholds.

    Median profit and median freight ratio are used
    to divide vendors into relative performance groups.
    """

    profit_threshold = df[
        "EstimatedProfitAfterFreight"
    ].median()

    freight_threshold = df[
        "FreightToRevenueRatio"
    ].median()

    print("\nClassification thresholds:")
    print(f"Median profit after freight: {profit_threshold:.2f}")
    print(f"Median freight-to-revenue ratio: {freight_threshold:.4f}")

    return profit_threshold, freight_threshold


# --------------------------------------------------
# 5. Classify vendors
# --------------------------------------------------

def classify_vendors(df, profit_threshold, freight_threshold):
    """Assign a business category to each vendor."""

    df = df.copy()

    high_profit = (
        df["EstimatedProfitAfterFreight"] >= profit_threshold
    )

    high_freight_ratio = (
        df["FreightToRevenueRatio"] > freight_threshold
    )

    conditions = [
        high_profit & ~high_freight_ratio,
        high_profit & high_freight_ratio,
        ~high_profit & high_freight_ratio,
        ~high_profit & ~high_freight_ratio,
    ]

    categories = [
        "Strong Performer",
        "Profitable but Costly",
        "Needs Attention",
        "Low Profitability",
    ]

    df["PerformanceCategory"] = np.select(
        conditions,
        categories,
        default="Unclassified",
    )

    return df


# --------------------------------------------------
# 6. Validate classification
# --------------------------------------------------

def validate_classification(df, original_rows):
    """Check the generated classifications."""

    allowed_categories = {
        "Strong Performer",
        "Profitable but Costly",
        "Needs Attention",
        "Low Profitability",
    }

    assert len(df) == original_rows, (
        "Row count changed during classification."
    )

    assert not df["VendorNumber"].duplicated().any(), (
        "Duplicate vendors found after classification."
    )

    assert df["PerformanceCategory"].notna().all(), (
        "Missing performance categories found."
    )

    actual_categories = set(
        df["PerformanceCategory"].unique()
    )

    unexpected_categories = actual_categories - allowed_categories

    assert not unexpected_categories, (
        f"Unexpected categories: {unexpected_categories}"
    )

    print("\nClassification validation passed.")
    print(f"Vendor records preserved: {len(df)}")
    print(f"Categories assigned: {df['PerformanceCategory'].notna().sum()}")


# --------------------------------------------------
# 7. Save results
# --------------------------------------------------

def save_results(df):
    """Save classified vendor data."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nOutput saved to:\n{OUTPUT_FILE}")


# --------------------------------------------------
# 8. Main execution
# --------------------------------------------------

def main():

    df = load_data()

    validate_input(df)

    original_rows = len(df)

    profit_threshold, freight_threshold = calculate_thresholds(df)

    df = classify_vendors(
        df,
        profit_threshold,
        freight_threshold,
    )

    validate_classification(df, original_rows)

    save_results(df)

    print("\nClassification distribution:")
    print(
        df["PerformanceCategory"]
        .value_counts()
        .to_string()
    )

    print("\nSample classified vendors:")

    print(
        df[
            [
                "VendorNumber",
                "VendorName",
                "EstimatedProfitAfterFreight",
                "FreightToRevenueRatio",
                "PerformanceCategory",
            ]
        ]
        .sort_values(
            "EstimatedProfitAfterFreight",
            ascending=False,
        )
        .head(10)
        .to_string(index=False)
    )

    print("\nVendor classification completed successfully!")


if __name__ == "__main__":
    main()