import sqlite3
from pathlib import Path

import pandas as pd


# ==================================================
# 1. PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATABASE_DIR = PROJECT_ROOT / "data"

DATABASE_PATH = DATABASE_DIR / "vendor_iq.db"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. DATABASE TABLE CONFIGURATION
# ==================================================

TABLES = {
    "vendors": "vendors.csv",
    "purchase_prices": "purchase_prices.csv",
    "purchases": "purchases.csv",
    "sales": "sales.csv",
    "vendor_invoice": "vendor_invoice.csv"
}


# ==================================================
# 3. CONNECT TO SQLITE DATABASE
# ==================================================

connection = sqlite3.connect(DATABASE_PATH)

print(f"Connected to database: {DATABASE_PATH}")


try:

    # ==================================================
    # 4. LOAD CSV FILES INTO SQLITE TABLES
    # ==================================================

    for table_name, file_name in TABLES.items():

        file_path = RAW_DATA_DIR / file_name

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required CSV file not found: {file_path}"
            )

        dataframe = pd.read_csv(file_path)

        dataframe.to_sql(
            name=table_name,
            con=connection,
            if_exists="replace",
            index=False
        )

        print(
            f"Loaded {len(dataframe)} rows "
            f"into table '{table_name}'"
        )

    # ==================================================
    # 5. VERIFY DATABASE TABLES
    # ==================================================

    cursor = connection.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """)

    tables = cursor.fetchall()

    print("\nTables created in database:")

    for table in tables:
        print("-", table[0])

    # ==================================================
    # 6. VERIFY ROW COUNTS
    # ==================================================

    print("\nRow counts:")

    for table_name in TABLES:

        cursor.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        )

        row_count = cursor.fetchone()[0]

        print(f"{table_name}: {row_count:,} rows")

    # ==================================================
    # 7. CHECK COLUMN NAMES
    # ==================================================

    print("\nTable schemas:")

    for table_name in TABLES:

        cursor.execute(
            f'PRAGMA table_info("{table_name}")'
        )

        columns = cursor.fetchall()

        column_names = [
            column[1] for column in columns
        ]

        print(f"{table_name}: {column_names}")

    print("\nDatabase creation and verification completed!")

finally:

    connection.close()

    print("\nDatabase connection closed.")