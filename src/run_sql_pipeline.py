import sqlite3
from pathlib import Path

import pandas as pd


# ==================================================
# 1. PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "vendor_iq.db"
SQL_FILE_PATH = PROJECT_ROOT / "sql" / "vendor_analytics.sql"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = PROCESSED_DIR / "vendor_performance.csv"


# ==================================================
# 2. CHECK REQUIRED FILES
# ==================================================

if not DATABASE_PATH.exists():
    raise FileNotFoundError(
        f"Database not found: {DATABASE_PATH}"
    )

if not SQL_FILE_PATH.exists():
    raise FileNotFoundError(
        f"SQL file not found: {SQL_FILE_PATH}"
    )


# ==================================================
# 3. READ SQL QUERY
# ==================================================

with open(SQL_FILE_PATH, "r", encoding="utf-8") as file:
    sql_query = file.read()

print("SQL query loaded successfully.")


# ==================================================
# 4. EXECUTE SQL QUERY
# ==================================================

connection = sqlite3.connect(DATABASE_PATH)

try:

    dataframe = pd.read_sql_query(
        sql_query,
        connection
    )

    print("\nSQL query executed successfully.")

finally:

    connection.close()


# ==================================================
# 5. VALIDATE QUERY OUTPUT
# ==================================================

print("\nOutput validation:")

print("Total rows:", len(dataframe))
print("Total columns:", len(dataframe.columns))

print("\nColumn names:")
print(dataframe.columns.tolist())


# Check expected number of vendors.
if len(dataframe) != 100:
    raise ValueError(
        f"Expected 100 vendor rows, got {len(dataframe)}"
    )


# Check duplicate vendor IDs.
if dataframe["VendorNumber"].duplicated().any():
    raise ValueError(
        "Duplicate VendorNumber found in output."
    )


# Check missing vendor identifiers.
if dataframe["VendorNumber"].isna().any():
    raise ValueError(
        "Missing VendorNumber found in output."
    )


print("\nAll output validation checks passed.")


# ==================================================
# 6. SAVE PROCESSED DATASET
# ==================================================

dataframe.to_csv(
    OUTPUT_PATH,
    index=False
)

print(f"\nDataset saved to: {OUTPUT_PATH}")


# ==================================================
# 7. DISPLAY SAMPLE OUTPUT
# ==================================================

print("\nTop 10 vendors by estimated profit after freight:")

print(
    dataframe[
        [
            "VendorNumber",
            "VendorName",
            "TotalSalesRevenue",
            "GrossProfit",
            "TotalFreightCost",
            "EstimatedProfitAfterFreight"
        ]
    ].head(10).to_string(index=False)
)


# ==================================================
# 8. DISPLAY BASIC STATISTICS
# ==================================================

print("\nBasic statistics:")

print(
    dataframe[
        [
            "TotalPurchaseAmount",
            "TotalSalesRevenue",
            "GrossProfit",
            "EstimatedProfitAfterFreight"
        ]
    ].describe().round(2)
)


print("\nVendorIQ SQL analytics pipeline completed!")