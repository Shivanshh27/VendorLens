"""
VendorIQ - Feature Engineering

Creates additional analytical features from the cleaned vendor performance data.
Input:  data/processed/vendor_performance_clean.csv
Output: data/processed/vendor_features.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# 1. Define project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vendor_performance_clean.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vendor_features.csv"
)


# --------------------------------------------------
# 2. Load cleaned data
# --------------------------------------------------

def load_data():
    """Load the cleaned vendor performance dataset."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print("=" * 60)
    print("VENDORIQ - FEATURE ENGINEERING")
    print("=" * 60)

    print(f"Input file: {INPUT_FILE.name}")
    print(f"Original dataset shape: {df.shape}")

    return df


# --------------------------------------------------
# 3. Validate input dataset
# --------------------------------------------------

def validate_input(df):
    """Check whether the input dataset has the required columns."""

    required_columns = [
        "VendorNumber",
        "TotalPurchaseTransactions",
        "TotalPurchaseQuantity",
        "TotalPurchaseAmount",
        "TotalSalesTransactions",
        "TotalSalesRevenue",
        "GrossProfit",
        "TotalFreightCost",
        "EstimatedRemainingInventory",
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

    if df["VendorNumber"].duplicated().any():
        raise ValueError("Duplicate vendor records found.")

    if df["VendorNumber"].isna().any():
        raise ValueError("VendorNumber contains missing values.")

    print("\nInput validation passed.")


# --------------------------------------------------
# 4. Safe division helper
# --------------------------------------------------

def safe_divide(numerator, denominator):
    """
    Divide two pandas Series safely.

    If the denominator is zero, the result is NaN
    because the ratio is mathematically undefined.
    """

    denominator = denominator.replace(0, np.nan)

    return numerator.div(denominator)


# --------------------------------------------------
# 5. Create new features
# --------------------------------------------------

def create_features(df):
    """Create additional analytical features for each vendor."""

    df = df.copy()

    # Feature 1:
    # Freight cost as a proportion of sales revenue.
    df["FreightToRevenueRatio"] = safe_divide(
        df["TotalFreightCost"],
        df["TotalSalesRevenue"],
    )

    # Feature 2:
    # Purchase amount compared with sales revenue.
    # This is descriptive, not an accounting profit measure.
    df["PurchaseToSalesValueRatio"] = safe_divide(
        df["TotalPurchaseAmount"],
        df["TotalSalesRevenue"],
    )

    # Feature 3:
    # Average gross profit generated per sales transaction.
    df["GrossProfitPerSalesTransaction"] = safe_divide(
        df["GrossProfit"],
        df["TotalSalesTransactions"],
    )

    # Feature 4:
    # Average purchase transaction value.
    df["AveragePurchaseTransactionValue"] = safe_divide(
        df["TotalPurchaseAmount"],
        df["TotalPurchaseTransactions"],
    )

    # Feature 5:
    # Proportion of purchased units that remain unsold.
    df["UnsoldInventoryRatio"] = safe_divide(
        df["EstimatedRemainingInventory"],
        df["TotalPurchaseQuantity"],
    )

    return df


# --------------------------------------------------
# 6. Validate engineered features
# --------------------------------------------------

def validate_features(df, original_rows):
    """Validate the output after feature engineering."""

    new_features = [
        "FreightToRevenueRatio",
        "PurchaseToSalesValueRatio",
        "GrossProfitPerSalesTransaction",
        "AveragePurchaseTransactionValue",
        "UnsoldInventoryRatio",
    ]

    # Check row count.
    assert len(df) == original_rows, (
        "Row count changed during feature engineering."
    )

    # Check vendor uniqueness.
    assert not df["VendorNumber"].duplicated().any(), (
        "Duplicate vendors found after feature engineering."
    )

    # Check for infinite values.
    for column in new_features:
        assert not np.isinf(df[column].dropna()).any(), (
            f"Infinite values found in {column}."
        )

    # Check that freight ratio is non-negative.
    valid_freight_ratios = df["FreightToRevenueRatio"].dropna()

    assert (valid_freight_ratios >= 0).all(), (
        "Negative freight-to-revenue ratios found."
    )

    # In this project's synthetic data, unsold inventory
    # should be between 0 and 1.
    valid_inventory_ratios = df["UnsoldInventoryRatio"].dropna()

    assert (
        (valid_inventory_ratios >= 0)
        & (valid_inventory_ratios <= 1)
    ).all(), "Unexpected unsold inventory ratios found."

    print("\nFeature validation passed.")
    print(f"Vendor rows preserved: {len(df)}")
    print("Duplicate vendors: 0")
    print("Infinite feature values: 0")

    print("\nMissing values in engineered features:")

    for column in new_features:
        missing_count = int(df[column].isna().sum())
        print(f"{column}: {missing_count}")


# --------------------------------------------------
# 7. Save feature dataset
# --------------------------------------------------

def save_data(df):
    """Save the engineered dataset without overwriting the input."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nFeature dataset saved to:\n{OUTPUT_FILE}")


# --------------------------------------------------
# 8. Main execution
# --------------------------------------------------

def main():

    # Load and validate the input data.
    df = load_data()
    validate_input(df)

    original_rows = len(df)

    # Create new features.
    df = create_features(df)

    # Validate the final dataset.
    validate_features(df, original_rows)

    # Save the output.
    save_data(df)

    print("\nNew features created:")

    print(
        df[
            [
                "VendorNumber",
                "FreightToRevenueRatio",
                "PurchaseToSalesValueRatio",
                "GrossProfitPerSalesTransaction",
                "AveragePurchaseTransactionValue",
                "UnsoldInventoryRatio",
            ]
        ].head(5).to_string(index=False)
    )

    print("\nFinal dataset shape:", df.shape)
    print("\nFeature engineering completed successfully!")


if __name__ == "__main__":
    main()