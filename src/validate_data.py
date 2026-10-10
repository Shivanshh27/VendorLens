import sqlite3
from pathlib import Path


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "vendor_iq.db"


# ==================================================
# 2. DATABASE CONNECTION
# ==================================================

connection = sqlite3.connect(DATABASE_PATH)

print("=" * 60)
print("             VENDORIQ DATA VALIDATION")
print("=" * 60)

validation_results = []


# ==================================================
# 3. VALIDATION HELPER FUNCTION
# ==================================================

def run_check(check_name, query, expected_result=0):

    cursor = connection.cursor()
    cursor.execute(query)

    actual_result = cursor.fetchone()[0]

    passed = actual_result == expected_result

    status = "PASS" if passed else "FAIL"

    validation_results.append({
        "Check": check_name,
        "Actual Result": actual_result,
        "Expected Result": expected_result,
        "Status": status
    })

    print(f"\n[{status}] {check_name}")
    print(f"       Actual: {actual_result}")
    print(f"       Expected: {expected_result}")


# ==================================================
# 4. DUPLICATE PRIMARY-KEY CHECKS
# ==================================================

run_check(
    "Duplicate vendor IDs",
    """
    SELECT COUNT(*)
    FROM (
        SELECT VendorNumber
        FROM vendors
        GROUP BY VendorNumber
        HAVING COUNT(*) > 1
    );
    """
)

run_check(
    "Duplicate product IDs",
    """
    SELECT COUNT(*)
    FROM (
        SELECT Brand
        FROM purchase_prices
        GROUP BY Brand
        HAVING COUNT(*) > 1
    );
    """
)

run_check(
    "Duplicate purchase IDs",
    """
    SELECT COUNT(*)
    FROM (
        SELECT PurchaseID
        FROM purchases
        GROUP BY PurchaseID
        HAVING COUNT(*) > 1
    );
    """
)

run_check(
    "Duplicate sales IDs",
    """
    SELECT COUNT(*)
    FROM (
        SELECT SalesID
        FROM sales
        GROUP BY SalesID
        HAVING COUNT(*) > 1
    );
    """
)

run_check(
    "Duplicate invoice IDs",
    """
    SELECT COUNT(*)
    FROM (
        SELECT InvoiceID
        FROM vendor_invoice
        GROUP BY InvoiceID
        HAVING COUNT(*) > 1
    );
    """
)


# ==================================================
# 5. REFERENTIAL INTEGRITY CHECKS
# ==================================================

run_check(
    "Purchases with unknown vendors",
    """
    SELECT COUNT(*)
    FROM purchases p
    LEFT JOIN vendors v
        ON p.VendorNumber = v.VendorNumber
    WHERE v.VendorNumber IS NULL;
    """
)

run_check(
    "Sales with unknown vendors",
    """
    SELECT COUNT(*)
    FROM sales s
    LEFT JOIN vendors v
        ON s.VendorNumber = v.VendorNumber
    WHERE v.VendorNumber IS NULL;
    """
)

run_check(
    "Purchases with unknown products",
    """
    SELECT COUNT(*)
    FROM purchases p
    LEFT JOIN purchase_prices pp
        ON p.Brand = pp.Brand
    WHERE pp.Brand IS NULL;
    """
)

run_check(
    "Sales with unknown products",
    """
    SELECT COUNT(*)
    FROM sales s
    LEFT JOIN purchase_prices pp
        ON s.Brand = pp.Brand
    WHERE pp.Brand IS NULL;
    """
)

run_check(
    "Invoices with unknown vendors",
    """
    SELECT COUNT(*)
    FROM vendor_invoice i
    LEFT JOIN vendors v
        ON i.VendorNumber = v.VendorNumber
    WHERE v.VendorNumber IS NULL;
    """
)


# ==================================================
# 6. NULL-VALUE CHECKS
# ==================================================

run_check(
    "Purchases with missing vendor or product IDs",
    """
    SELECT COUNT(*)
    FROM purchases
    WHERE VendorNumber IS NULL
       OR Brand IS NULL;
    """
)

run_check(
    "Sales with missing vendor or product IDs",
    """
    SELECT COUNT(*)
    FROM sales
    WHERE VendorNumber IS NULL
       OR Brand IS NULL;
    """
)

run_check(
    "Products with missing prices",
    """
    SELECT COUNT(*)
    FROM purchase_prices
    WHERE PurchasePrice IS NULL
       OR ActualPrice IS NULL;
    """
)


# ==================================================
# 7. BUSINESS-RULE CHECKS
# ==================================================

run_check(
    "Purchases with invalid quantities",
    """
    SELECT COUNT(*)
    FROM purchases
    WHERE Quantity IS NULL
       OR Quantity <= 0;
    """
)

run_check(
    "Sales with invalid quantities",
    """
    SELECT COUNT(*)
    FROM sales
    WHERE SalesQuantity IS NULL
       OR SalesQuantity <= 0;
    """
)

run_check(
    "Products with non-positive prices",
    """
    SELECT COUNT(*)
    FROM purchase_prices
    WHERE PurchasePrice <= 0
       OR ActualPrice <= 0;
    """
)

run_check(
    "Purchases with negative amounts",
    """
    SELECT COUNT(*)
    FROM purchases
    WHERE Dollars < 0;
    """
)

run_check(
    "Sales with negative amounts",
    """
    SELECT COUNT(*)
    FROM sales
    WHERE SalesDollars < 0;
    """
)

run_check(
    "Invoices with negative freight",
    """
    SELECT COUNT(*)
    FROM vendor_invoice
    WHERE Freight < 0;
    """
)


# ==================================================
# 8. FINANCIAL CONSISTENCY CHECKS
# ==================================================

run_check(
    "Purchase amount calculation mismatches",
    """
    SELECT COUNT(*)
    FROM purchases p
    JOIN purchase_prices pp
        ON p.Brand = pp.Brand
    WHERE ABS(
        p.Dollars - (p.Quantity * pp.PurchasePrice)
    ) > 0.011;
    """
)

run_check(
    "Sales amount calculation mismatches",
    """
    SELECT COUNT(*)
    FROM sales
    WHERE ABS(
        SalesDollars - (SalesQuantity * SalesPrice)
    ) > 0.011;
    """
)


# ==================================================
# 9. INVENTORY CONSISTENCY CHECK
# ==================================================

run_check(
    "Vendor-product pairs with sales exceeding purchases",
    """
    SELECT COUNT(*)
    FROM (
        SELECT
            p.VendorNumber,
            p.Brand,
            SUM(p.Quantity) AS PurchasedQuantity
        FROM purchases p
        GROUP BY p.VendorNumber, p.Brand
    ) purchased
    JOIN (
        SELECT
            s.VendorNumber,
            s.Brand,
            SUM(s.SalesQuantity) AS SoldQuantity
        FROM sales s
        GROUP BY s.VendorNumber, s.Brand
    ) sold
        ON purchased.VendorNumber = sold.VendorNumber
       AND purchased.Brand = sold.Brand
    WHERE sold.SoldQuantity > purchased.PurchasedQuantity;
    """
)


# ==================================================
# 10. VALIDATION SUMMARY
# ==================================================

print("\n" + "=" * 60)
print("                 VALIDATION SUMMARY")
print("=" * 60)

total_checks = len(validation_results)

passed_checks = sum(
    1 for result in validation_results
    if result["Status"] == "PASS"
)

failed_checks = total_checks - passed_checks

print(f"Total checks : {total_checks}")
print(f"Passed       : {passed_checks}")
print(f"Failed       : {failed_checks}")

if failed_checks == 0:
    print("\nAll data quality checks passed!")
else:
    print("\nSome data quality checks failed.")
    print("Review the failed checks before proceeding.")


# ==================================================
# 11. SAVE VALIDATION REPORT
# ==================================================

import pandas as pd

report_df = pd.DataFrame(validation_results)

OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = OUTPUT_DIR / "validation_report.csv"

report_df.to_csv(REPORT_PATH, index=False)

print(f"\nValidation report saved to: {REPORT_PATH}")


# ==================================================
# 12. CLOSE CONNECTION
# ==================================================

connection.close()

print("\nDatabase connection closed.")