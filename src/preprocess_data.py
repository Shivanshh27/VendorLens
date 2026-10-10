import pandas as pd
from pathlib import Path


# ==================================================
# 1. PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vendor_performance.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "vendor_performance_clean.csv"


# ==================================================
# 2. REQUIRED COLUMNS
# ==================================================

REQUIRED_COLUMNS = [
    "VendorNumber",
    "VendorName",
    "TotalPurchaseTransactions",
    "TotalPurchaseQuantity",
    "TotalPurchaseAmount",
    "TotalSalesTransactions",
    "TotalSalesQuantity",
    "TotalSalesRevenue",
    "EstimatedCOGS",
    "GrossProfit",
    "GrossProfitMarginPercent",
    "TotalExciseTax",
    "TotalInvoices",
    "TotalFreightCost",
    "AverageFreightPerInvoice",
    "EstimatedProfitAfterFreight",
    "EstimatedRemainingInventory",
    "SalesToPurchaseQuantityRatio"
]


# ==================================================
# 3. LOAD DATA
# ==================================================

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Input dataset not found: {INPUT_PATH}"
    )

df = pd.read_csv(INPUT_PATH)

print("=" * 60)
print("       VENDORIQ PYTHON PREPROCESSING PIPELINE")
print("=" * 60)

print("\nOriginal dataset shape:", df.shape)


# ==================================================
# 4. SCHEMA VALIDATION
# ==================================================

missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

# Keep the expected columns in a consistent order.
df = df[REQUIRED_COLUMNS].copy()

print("\nPASS: All required columns are present.")


# ==================================================
# 5. DUPLICATE CHECK
# ==================================================

duplicate_vendor_count = df["VendorNumber"].duplicated().sum()

print(
    "\nDuplicate vendor records:",
    duplicate_vendor_count
)

if duplicate_vendor_count > 0:
    raise ValueError(
        "Duplicate VendorNumber values detected."
    )


# ==================================================
# 6. MISSING VALUE ANALYSIS
# ==================================================

missing_values = df.isnull().sum()

print("\nMissing values by column:")

print(missing_values[missing_values > 0])

total_missing_values = int(missing_values.sum())

print(
    "\nTotal missing values:",
    total_missing_values
)


# ==================================================
# 7. DATA TYPE VALIDATION
# ==================================================

NUMERIC_COLUMNS = [
    column
    for column in REQUIRED_COLUMNS
    if column not in ["VendorName"]
]

for column in NUMERIC_COLUMNS:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

print("\nNumeric column conversion completed.")


# ==================================================
# 8. MISSING VALUE HANDLING
# ==================================================

# VendorNumber and VendorName are identifiers.
# Missing identifiers should not be silently replaced.

if df["VendorNumber"].isnull().any():
    raise ValueError(
        "VendorNumber contains missing or invalid values."
    )

if df["VendorName"].isnull().any():
    raise ValueError(
        "VendorName contains missing values."
    )

# For this generated dataset, missing numeric values
# indicate a data quality issue. Do not silently fill them.

numeric_missing = df[NUMERIC_COLUMNS].isnull().sum()

if numeric_missing.sum() > 0:
    raise ValueError(
        "Missing or invalid numeric values detected:\n"
        f"{numeric_missing[numeric_missing > 0]}"
    )

print("PASS: No missing or invalid numeric values.")


# ==================================================
# 9. BUSINESS RULE VALIDATION
# ==================================================

NON_NEGATIVE_COLUMNS = [
    "TotalPurchaseTransactions",
    "TotalPurchaseQuantity",
    "TotalPurchaseAmount",
    "TotalSalesTransactions",
    "TotalSalesQuantity",
    "TotalSalesRevenue",
    "EstimatedCOGS",
    "TotalExciseTax",
    "TotalInvoices",
    "TotalFreightCost",
    "AverageFreightPerInvoice",
    "EstimatedRemainingInventory"
]

for column in NON_NEGATIVE_COLUMNS:

    invalid_count = int((df[column] < 0).sum())

    print(
        f"{column}: {invalid_count} negative values"
    )

    if invalid_count > 0:
        raise ValueError(
            f"Unexpected negative values in {column}"
        )


# ==================================================
# 10. FINANCIAL CONSISTENCY CHECKS
# ==================================================

expected_gross_profit = (
    df["TotalSalesRevenue"] - df["EstimatedCOGS"]
)

gross_profit_difference = (
    df["GrossProfit"] - expected_gross_profit
).abs()

if (gross_profit_difference > 0.011).any():
    raise ValueError(
        "GrossProfit does not match revenue minus estimated COGS."
    )

print("\nPASS: Gross profit formula verified.")


expected_profit_after_freight = (
    df["GrossProfit"] - df["TotalFreightCost"]
)

profit_difference = (
    df["EstimatedProfitAfterFreight"]
    - expected_profit_after_freight
).abs()

if (profit_difference > 0.011).any():
    raise ValueError(
        "EstimatedProfitAfterFreight formula mismatch."
    )

print("PASS: Estimated profit formula verified.")


# ==================================================
# 11. RATIO VALIDATION
# ==================================================

expected_ratio = (
    df["TotalSalesQuantity"]
    / df["TotalPurchaseQuantity"].replace(0, float("nan"))
)

ratio_difference = (
    df["SalesToPurchaseQuantityRatio"] - expected_ratio
).abs()

# The SQL output stores the ratio to four decimal places.
if (ratio_difference.dropna() > 0.00011).any():
    raise ValueError(
        "Sales-to-purchase quantity ratio mismatch."
    )

print("PASS: Sales-to-purchase quantity ratio verified.")


# ==================================================
# 12. INVENTORY VALIDATION
# ==================================================

expected_inventory = (
    df["TotalPurchaseQuantity"]
    - df["TotalSalesQuantity"]
)

inventory_difference = (
    df["EstimatedRemainingInventory"]
    - expected_inventory
).abs()

if (inventory_difference > 0.011).any():
    raise ValueError(
        "Estimated remaining inventory mismatch."
    )

print("PASS: Remaining inventory formula verified.")


# ==================================================
# 13. SAVE CLEAN DATASET
# ==================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n" + "=" * 60)
print("             PREPROCESSING SUMMARY")
print("=" * 60)

print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Duplicate vendors:", int(duplicate_vendor_count))
print("Missing values:", total_missing_values)

print("\nClean dataset saved to:")
print(OUTPUT_PATH)

print("\nPython preprocessing pipeline completed!")