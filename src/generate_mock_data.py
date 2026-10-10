import random
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ==================================================
# 1. CONFIGURATION
# ==================================================

SEED = 42

NUM_VENDORS = 100
NUM_PRODUCTS = 1000
NUM_PURCHASES = 50_000
NUM_SALES = 50_000
NUM_INVOICES = 2_000

random.seed(SEED)
np.random.seed(SEED)


# ==================================================
# 2. PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 3. GENERATE VENDORS
# ==================================================

vendors = pd.DataFrame({
    "VendorNumber": range(1001, 1001 + NUM_VENDORS),
    "VendorName": [
        f"Vendor_{i:03d}"
        for i in range(1, NUM_VENDORS + 1)
    ]
})

print("Vendors generated:", len(vendors))


# ==================================================
# 4. GENERATE PRODUCT / PURCHASE PRICE DATA
# ==================================================

products = pd.DataFrame({
    "Brand": range(50001, 50001 + NUM_PRODUCTS),
    "Description": [
        f"Product_{i:04d}"
        for i in range(1, NUM_PRODUCTS + 1)
    ],
    "Volume": np.random.choice(
        [375, 500, 700, 750, 1000, 1500, 1750],
        size=NUM_PRODUCTS
    ),
    "PurchasePrice": np.round(
        np.random.uniform(5, 100, NUM_PRODUCTS),
        2
    ),
    "ActualPrice": np.round(
        np.random.uniform(10, 150, NUM_PRODUCTS),
        2
    )
})

# Ensure selling price is greater than purchase price.
products["ActualPrice"] = np.maximum(
    products["ActualPrice"],
    products["PurchasePrice"] + 2
)

print("Products generated:", len(products))


# ==================================================
# 5. GENERATE PURCHASE TRANSACTIONS
# ==================================================

purchase_vendor_ids = np.random.choice(
    vendors["VendorNumber"],
    size=NUM_PURCHASES
)

purchase_product_ids = np.random.choice(
    products["Brand"],
    size=NUM_PURCHASES
)

purchase_quantities = np.random.randint(
    10,
    101,
    size=NUM_PURCHASES
)

purchase_df = pd.DataFrame({
    "PurchaseID": range(1, NUM_PURCHASES + 1),
    "VendorNumber": purchase_vendor_ids,
    "Brand": purchase_product_ids,
    "Quantity": purchase_quantities
})

purchase_df = purchase_df.merge(
    products[["Brand", "PurchasePrice"]],
    on="Brand",
    how="left",
    validate="many_to_one"
)

purchase_df["Dollars"] = np.round(
    purchase_df["Quantity"] * purchase_df["PurchasePrice"],
    2
)

purchase_df["PurchaseDate"] = pd.to_datetime(
    np.random.choice(
        pd.date_range("2025-01-01", "2025-12-31"),
        size=NUM_PURCHASES
    )
)

purchase_df = purchase_df[
    [
        "PurchaseID",
        "VendorNumber",
        "Brand",
        "Quantity",
        "Dollars",
        "PurchaseDate"
    ]
]

print("Purchase transactions generated:", len(purchase_df))


# ==================================================
# 6. GENERATE SALES TRANSACTIONS
# ==================================================

# Calculate total purchased quantity for each vendor-product pair.
available_stock = (
    purchase_df.groupby(
        ["VendorNumber", "Brand"],
        as_index=False
    )["Quantity"]
    .sum()
    .rename(columns={"Quantity": "AvailableQuantity"})
)

# Only generate sales for vendor-product combinations
# that actually exist in purchase records.
sales_pairs = available_stock[
    available_stock["AvailableQuantity"] >= 1
].copy()

sales_pairs = sales_pairs.reset_index(drop=True)

# Assign a vendor-product pair to each sales transaction.
sales_pair_indices = np.random.randint(
    0,
    len(sales_pairs),
    size=NUM_SALES
)

sales_df = sales_pairs.iloc[
    sales_pair_indices
][
    ["VendorNumber", "Brand", "AvailableQuantity"]
].reset_index(drop=True)

# Each transaction sells one unit.
# This ensures aggregate sales cannot exceed aggregate purchases
# for any vendor-product pair.
sales_df["SalesQuantity"] = 1

sales_df["SalesID"] = range(1, NUM_SALES + 1)

sales_df["SalesDate"] = pd.to_datetime(
    np.random.choice(
        pd.date_range("2025-01-01", "2025-12-31"),
        size=NUM_SALES
    )
)

sales_df = sales_df.merge(
    products[["Brand", "PurchasePrice", "ActualPrice"]],
    on="Brand",
    how="left",
    validate="many_to_one"
)

# Selling price includes a random discount.
discount = np.random.uniform(
    0.90,
    1.00,
    size=NUM_SALES
)

sales_df["SalesPrice"] = np.round(
    sales_df["ActualPrice"] * discount,
    2
)

sales_df["SalesDollars"] = np.round(
    sales_df["SalesQuantity"] * sales_df["SalesPrice"],
    2
)

sales_df["ExciseTax"] = np.round(
    np.random.uniform(0.1, 3.0, size=NUM_SALES),
    2
)

sales_df = sales_df[
    [
        "SalesID",
        "VendorNumber",
        "Brand",
        "SalesQuantity",
        "SalesDollars",
        "SalesPrice",
        "ExciseTax",
        "SalesDate"
    ]
]

print("Sales transactions generated:", len(sales_df))


# ==================================================
# 7. GENERATE VENDOR INVOICES
# ==================================================

invoice_vendor_ids = np.random.choice(
    vendors["VendorNumber"],
    size=NUM_INVOICES
)

invoice_df = pd.DataFrame({
    "InvoiceID": range(1, NUM_INVOICES + 1),
    "VendorNumber": invoice_vendor_ids,
    "InvoiceDate": pd.to_datetime(
        np.random.choice(
            pd.date_range("2025-01-01", "2025-12-31"),
            size=NUM_INVOICES
        )
    ),
    "Freight": np.round(
        np.random.uniform(10, 500, NUM_INVOICES),
        2
    )
})

print("Vendor invoices generated:", len(invoice_df))


# ==================================================
# 8. SAVE RAW DATA AS CSV FILES
# ==================================================

datasets = {
    "vendors.csv": vendors,
    "purchase_prices.csv": products,
    "purchases.csv": purchase_df,
    "sales.csv": sales_df,
    "vendor_invoice.csv": invoice_df
}

for filename, dataframe in datasets.items():
    file_path = RAW_DATA_DIR / filename

    dataframe.to_csv(
        file_path,
        index=False
    )

    print(f"Saved: {file_path}")


# ==================================================
# 9. DATA VALIDATION
# ==================================================

assert len(vendors) == NUM_VENDORS
assert len(products) == NUM_PRODUCTS
assert len(purchase_df) == NUM_PURCHASES
assert len(sales_df) == NUM_SALES
assert len(invoice_df) == NUM_INVOICES

assert purchase_df["VendorNumber"].isin(
    vendors["VendorNumber"]
).all()

assert sales_df["VendorNumber"].isin(
    vendors["VendorNumber"]
).all()

assert purchase_df["Brand"].isin(
    products["Brand"]
).all()

assert sales_df["Brand"].isin(
    products["Brand"]
).all()

print("\nAll basic validation checks passed.")

print("\nDataset shapes:")

for filename, dataframe in datasets.items():
    print(f"{filename}: {dataframe.shape}")

print("\nSynthetic raw data generation completed successfully!")