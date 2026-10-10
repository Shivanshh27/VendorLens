import sqlite3
from pathlib import Path

import pandas as pd


# ==================================================
# 1. PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "vendor_iq.db"

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vendor_performance.csv"
)


# ==================================================
# 2. CHECK REQUIRED FILES
# ==================================================

if not DATABASE_PATH.exists():
    raise FileNotFoundError(
        f"Database not found: {DATABASE_PATH}"
    )

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Analytics dataset not found: {DATASET_PATH}"
    )


# ==================================================
# 3. LOAD ANALYTICAL DATASET
# ==================================================

df = pd.read_csv(DATASET_PATH)

print("=" * 60)
print("       VENDORIQ ANALYTICS VERIFICATION")
print("=" * 60)

print("\nDataset shape:", df.shape)


# ==================================================
# 4. BASIC DATASET CHECKS
# ==================================================

assert len(df) == 100, (
    f"Expected 100 vendors, found {len(df)}"
)

assert df["VendorNumber"].nunique() == 100, (
    "VendorNumber contains duplicate values."
)

assert not df["VendorNumber"].isna().any(), (
    "VendorNumber contains missing values."
)

print("\nPASS: 100 unique vendors found.")


# ==================================================
# 5. INDEPENDENTLY RECOMPUTE PURCHASE QUANTITIES
# ==================================================

connection = sqlite3.connect(DATABASE_PATH)

try:

    purchase_check = pd.read_sql_query(
        """
        SELECT
            VendorNumber,
            SUM(Quantity) AS RecomputedPurchaseQuantity
        FROM purchases
        GROUP BY VendorNumber;
        """,
        connection
    )

    sales_check = pd.read_sql_query(
        """
        SELECT
            VendorNumber,
            SUM(SalesQuantity) AS RecomputedSalesQuantity
        FROM sales
        GROUP BY VendorNumber;
        """,
        connection
    )

    purchase_amount_check = pd.read_sql_query(
        """
        SELECT
            VendorNumber,
            ROUND(SUM(Dollars), 2) AS RecomputedPurchaseAmount
        FROM purchases
        GROUP BY VendorNumber;
        """,
        connection
    )

    sales_revenue_check = pd.read_sql_query(
        """
        SELECT
            VendorNumber,
            ROUND(SUM(SalesDollars), 2) AS RecomputedSalesRevenue
        FROM sales
        GROUP BY VendorNumber;
        """,
        connection
    )

    freight_check = pd.read_sql_query(
        """
        SELECT
            VendorNumber,
            ROUND(SUM(Freight), 2) AS RecomputedFreight
        FROM vendor_invoice
        GROUP BY VendorNumber;
        """,
        connection
    )

finally:

    connection.close()


# ==================================================
# 6. COMPARE PURCHASE QUANTITIES
# ==================================================

df = df.merge(
    purchase_check,
    on="VendorNumber",
    how="left",
    validate="one_to_one"
)

purchase_quantity_match = (
    df["TotalPurchaseQuantity"]
    == df["RecomputedPurchaseQuantity"]
)

print(
    "\nPurchase quantity mismatches:",
    int((~purchase_quantity_match).sum())
)


# ==================================================
# 7. COMPARE SALES QUANTITIES
# ==================================================

df = df.merge(
    sales_check,
    on="VendorNumber",
    how="left",
    validate="one_to_one"
)

sales_quantity_match = (
    df["TotalSalesQuantity"]
    == df["RecomputedSalesQuantity"]
)

print(
    "Sales quantity mismatches:",
    int((~sales_quantity_match).sum())
)


# ==================================================
# 8. COMPARE PURCHASE AMOUNTS
# ==================================================

df = df.merge(
    purchase_amount_check,
    on="VendorNumber",
    how="left",
    validate="one_to_one"
)

purchase_amount_match = (
    (df["TotalPurchaseAmount"] - df["RecomputedPurchaseAmount"])
    .abs()
    < 0.011
)

print(
    "Purchase amount mismatches:",
    int((~purchase_amount_match).sum())
)


# ==================================================
# 9. COMPARE SALES REVENUE
# ==================================================

df = df.merge(
    sales_revenue_check,
    on="VendorNumber",
    how="left",
    validate="one_to_one"
)

sales_revenue_match = (
    (df["TotalSalesRevenue"] - df["RecomputedSalesRevenue"])
    .abs()
    < 0.011
)

print(
    "Sales revenue mismatches:",
    int((~sales_revenue_match).sum())
)


# ==================================================
# 10. COMPARE FREIGHT COST
# ==================================================

df = df.merge(
    freight_check,
    on="VendorNumber",
    how="left",
    validate="one_to_one"
)

df["RecomputedFreight"] = (
    df["RecomputedFreight"].fillna(0)
)

freight_match = (
    (df["TotalFreightCost"] - df["RecomputedFreight"])
    .abs()
    < 0.011
)

print(
    "Freight mismatches:",
    int((~freight_match).sum())
)


# ==================================================
# 11. VERIFY PROFIT FORMULAS
# ==================================================

expected_gross_profit = (
    df["TotalSalesRevenue"] - df["EstimatedCOGS"]
).round(2)

gross_profit_match = (
    (df["GrossProfit"] - expected_gross_profit)
    .abs()
    < 0.011
)

print(
    "Gross profit formula mismatches:",
    int((~gross_profit_match).sum())
)


expected_profit_after_freight = (
    df["GrossProfit"] - df["TotalFreightCost"]
).round(2)

net_profit_match = (
    (
        df["EstimatedProfitAfterFreight"]
        - expected_profit_after_freight
    ).abs()
    < 0.011
)

print(
    "Estimated profit formula mismatches:",
    int((~net_profit_match).sum())
)


# ==================================================
# 12. VERIFY INVENTORY CALCULATION
# ==================================================

expected_inventory = (
    df["TotalPurchaseQuantity"]
    - df["TotalSalesQuantity"]
)

inventory_match = (
    df["EstimatedRemainingInventory"]
    == expected_inventory
)

print(
    "Remaining inventory mismatches:",
    int((~inventory_match).sum())
)


# ==================================================
# 13. FINAL VERIFICATION SUMMARY
# ==================================================

checks = {
    "Unique vendor IDs": df["VendorNumber"].nunique() == 100,
    "Purchase quantities": purchase_quantity_match.all(),
    "Sales quantities": sales_quantity_match.all(),
    "Purchase amounts": purchase_amount_match.all(),
    "Sales revenue": sales_revenue_match.all(),
    "Freight costs": freight_match.all(),
    "Gross profit formula": gross_profit_match.all(),
    "Estimated profit formula": net_profit_match.all(),
    "Remaining inventory": inventory_match.all()
}

print("\n" + "=" * 60)
print("               FINAL VERIFICATION")
print("=" * 60)

for check_name, passed in checks.items():
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {check_name}")

passed_count = sum(checks.values())
total_checks = len(checks)

print(f"\nPassed: {passed_count}/{total_checks}")
print(f"Failed: {total_checks - passed_count}/{total_checks}")

if passed_count == total_checks:
    print("\nAll analytical verification checks passed!")
else:
    print(
        "\nSome checks failed. Investigate the mismatches "
        "before proceeding."
    )