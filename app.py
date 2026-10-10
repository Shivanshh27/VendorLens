"""
VendorIQ - Vendor Performance Analytics Dashboard
"""

from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# 1. Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="VendorIQ | Vendor Analytics",
    page_icon="📊",
    layout="wide",
)


# --------------------------------------------------
# 2. Define paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vendor_classification.csv"
)


# --------------------------------------------------
# 3. Load data
# --------------------------------------------------

@st.cache_data
def load_data():
    """Load classified vendor data."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    return pd.read_csv(DATA_FILE)


# --------------------------------------------------
# 4. Dashboard header
# --------------------------------------------------

st.title("📊 VendorIQ")

st.subheader("Vendor Performance Analytics & Intelligence Platform")

st.markdown(
    """
    Analyze vendor profitability, purchasing activity, sales performance,
    and freight costs through an interactive dashboard.
    """
)

st.divider()


# --------------------------------------------------
# 5. Load and validate dataset
# --------------------------------------------------

try:
    df = load_data()

except (FileNotFoundError, pd.errors.EmptyDataError) as error:
    st.error(str(error))
    st.stop()


required_columns = [
    "VendorNumber",
    "VendorName",
    "TotalSalesRevenue",
    "GrossProfit",
    "GrossProfitMarginPercent",
    "TotalFreightCost",
    "EstimatedProfitAfterFreight",
    "PerformanceCategory",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        f"Required columns are missing: {missing_columns}"
    )
    st.stop()


# --------------------------------------------------
# 6. Calculate dashboard metrics
# --------------------------------------------------

total_vendors = df["VendorNumber"].nunique()

total_sales_revenue = df["TotalSalesRevenue"].sum()

total_estimated_profit = df[
    "EstimatedProfitAfterFreight"
].sum()

average_gross_margin = df[
    "GrossProfitMarginPercent"
].mean()

total_freight_cost = df["TotalFreightCost"].sum()


# --------------------------------------------------
# 7. Display KPI cards
# --------------------------------------------------

st.header("Business Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Total Vendors",
    value=f"{total_vendors:,}",
)

col2.metric(
    label="Total Sales Revenue",
    value=f"{total_sales_revenue:,.2f}",
)

col3.metric(
    label="Estimated Profit After Freight",
    value=f"{total_estimated_profit:,.2f}",
)

col4.metric(
    label="Average Gross Margin",
    value=f"{average_gross_margin:.2f}%",
)

st.divider()


# --------------------------------------------------
# 8. Performance category distribution
# --------------------------------------------------

st.header("Vendor Performance Distribution")

category_counts = (
    df["PerformanceCategory"]
    .value_counts()
    .rename_axis("Performance Category")
    .reset_index(name="Number of Vendors")
)

left_chart, right_chart = st.columns(2)

with left_chart:

    st.subheader("Category Breakdown")

    st.bar_chart(
        category_counts.set_index("Performance Category")
    )

with right_chart:

    st.subheader("Vendor Distribution")

    st.dataframe(
        category_counts,
        width="stretch",
        hide_index=True,
    )


st.divider()

# --------------------------------------------------
# Interactive Vendor Analysis
# --------------------------------------------------

st.header("🔎 Interactive Vendor Analysis")

# 1. Vendor search
search_query = st.text_input(
    "Search Vendor by Name or ID",
    placeholder="e.g. Vendor_065 or 1065",
)

# 2. Performance category filter
categories = sorted(
    df["PerformanceCategory"].dropna().unique().tolist()
)

selected_categories = st.multiselect(
    "Filter by Performance Category",
    options=categories,
    default=categories,
)

# 3. Apply filters
filtered_df = df[
    df["PerformanceCategory"].isin(selected_categories)
].copy()

if search_query.strip():

    query = search_query.strip()

    name_match = filtered_df["VendorName"].astype(str).str.contains(
        query,
        case=False,
        na=False,
        regex=False,
    )

    id_match = filtered_df["VendorNumber"].astype(str).str.contains(
        query,
        regex=False,
    )

    filtered_df = filtered_df[name_match | id_match]

st.write(f"Matching vendors: {len(filtered_df)}")

# 4. Display filtered vendors
st.dataframe(
    filtered_df[
        [
            "VendorNumber",
            "VendorName",
            "TotalSalesRevenue",
            "GrossProfit",
            "TotalFreightCost",
            "EstimatedProfitAfterFreight",
            "PerformanceCategory",
        ]
    ].sort_values(
        "EstimatedProfitAfterFreight",
        ascending=False,
    ),
    width="stretch",
    hide_index=True,
)

# 5. Individual vendor details
st.subheader("Individual Vendor Details")

if filtered_df.empty:

    st.info("No vendors match your search and selected filters.")

else:

    vendor_options = filtered_df["VendorNumber"].tolist()

    selected_vendor = st.selectbox(
        "Select a Vendor",
        options=vendor_options,
        format_func=lambda vendor_id: (
            f"{filtered_df.loc[filtered_df['VendorNumber'] == vendor_id, 'VendorName'].iloc[0]}"
            f" (ID: {vendor_id})"
        ),
    )

    vendor = filtered_df[
        filtered_df["VendorNumber"] == selected_vendor
    ].iloc[0]

    st.write(f"### {vendor['VendorName']}")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Sales Revenue",
        f"{vendor['TotalSalesRevenue']:,.2f}",
    )

    col2.metric(
        "Gross Profit",
        f"{vendor['GrossProfit']:,.2f}",
    )

    col3.metric(
        "Estimated Profit After Freight",
        f"{vendor['EstimatedProfitAfterFreight']:,.2f}",
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Total Freight Cost",
        f"{vendor['TotalFreightCost']:,.2f}",
    )

    col5.metric(
        "Gross Profit Margin",
        f"{vendor['GrossProfitMarginPercent']:.2f}%",
    )

    col6.metric(
        "Performance Category",
        vendor["PerformanceCategory"],
    )

# --------------------------------------------------
# 9. Top 10 vendors
# --------------------------------------------------

st.header("🏆 Top 10 Vendors")

top_vendors = (
    df.sort_values(
        "EstimatedProfitAfterFreight",
        ascending=False,
    )
    [
        [
            "VendorNumber",
            "VendorName",
            "TotalSalesRevenue",
            "GrossProfit",
            "TotalFreightCost",
            "EstimatedProfitAfterFreight",
            "PerformanceCategory",
        ]
    ]
    .head(10)
    .reset_index(drop=True)
)

st.dataframe(
    top_vendors,
    width="stretch",
    hide_index=True,
)

# --------------------------------------------------
# 10. Freight analysis
# --------------------------------------------------

st.header("🚚 Freight Cost Analysis")

freight_analysis = (
    df[
        [
            "VendorName",
            "TotalFreightCost",
        ]
    ]
    .sort_values(
        "TotalFreightCost",
        ascending=False,
    )
    .head(10)
    .set_index("VendorName")
)

st.subheader("Top 10 Vendors by Freight Cost")

st.bar_chart(freight_analysis)


# --------------------------------------------------
# 11. Footer
# --------------------------------------------------

st.divider()

st.caption(
    "VendorIQ | Built with Python, Pandas, SQLite, SQL and Streamlit. "
    "All current vendor records are synthetically generated."
)

# --------------------------------------------------
# Vendor Comparison
# --------------------------------------------------

st.divider()

st.header("⚖️ Vendor Performance Comparison")

st.write(
    "Compare two vendors across revenue, profitability, "
    "freight costs, and performance categories."
)

vendor_list = (
    df[["VendorNumber", "VendorName"]]
    .drop_duplicates()
    .sort_values("VendorName")
)

if len(vendor_list) < 2:

    st.warning("At least two vendors are required for comparison.")

else:

    col1, col2 = st.columns(2)

    with col1:
        vendor_a_id = st.selectbox(
            "Select First Vendor",
            options=vendor_list["VendorNumber"].tolist(),
            format_func=lambda vendor_id: (
                f"{vendor_list.loc[vendor_list['VendorNumber'] == vendor_id, 'VendorName'].iloc[0]}"
                f" (ID: {vendor_id})"
            ),
            key="comparison_vendor_a",
        )

    with col2:
        vendor_b_options = vendor_list[
            vendor_list["VendorNumber"] != vendor_a_id
        ]["VendorNumber"].tolist()

        vendor_b_id = st.selectbox(
            "Select Second Vendor",
            options=vendor_b_options,
            format_func=lambda vendor_id: (
                f"{vendor_list.loc[vendor_list['VendorNumber'] == vendor_id, 'VendorName'].iloc[0]}"
                f" (ID: {vendor_id})"
            ),
            key="comparison_vendor_b",
        )

    vendor_a = df[df["VendorNumber"] == vendor_a_id].iloc[0]
    vendor_b = df[df["VendorNumber"] == vendor_b_id].iloc[0]

    comparison_columns = {
        "Sales Revenue": "TotalSalesRevenue",
        "Gross Profit": "GrossProfit",
        "Freight Cost": "TotalFreightCost",
        "Estimated Profit After Freight": "EstimatedProfitAfterFreight",
        "Gross Profit Margin (%)": "GrossProfitMarginPercent",
    }

    comparison_data = {
        "Metric": list(comparison_columns.keys()),
        str(vendor_a["VendorName"]): [
            vendor_a[column]
            for column in comparison_columns.values()
        ],
        str(vendor_b["VendorName"]): [
            vendor_b[column]
            for column in comparison_columns.values()
        ],
    }

    comparison_df = pd.DataFrame(comparison_data)

    st.subheader("Comparison Table")

    st.dataframe(
        comparison_df,
        width="stretch",
        hide_index=True,
    )
    # --------------------------------------------------
    # Vendor Comparison Chart
    # --------------------------------------------------

    st.subheader("Visual Performance Comparison")

    chart_data = pd.DataFrame(
        {
            "Vendor": [
                str(vendor_a["VendorName"]),
                str(vendor_b["VendorName"]),
            ],
            "Sales Revenue": [
                vendor_a["TotalSalesRevenue"],
                vendor_b["TotalSalesRevenue"],
            ],
            "Gross Profit": [
                vendor_a["GrossProfit"],
                vendor_b["GrossProfit"],
            ],
            "Freight Cost": [
                vendor_a["TotalFreightCost"],
                vendor_b["TotalFreightCost"],
            ],
            "Estimated Profit After Freight": [
                vendor_a["EstimatedProfitAfterFreight"],
                vendor_b["EstimatedProfitAfterFreight"],
            ],
        }
    )

    selected_metric = st.selectbox(
        "Select Metric to Compare",
        options=[
            "Sales Revenue",
            "Gross Profit",
            "Freight Cost",
            "Estimated Profit After Freight",
        ],
        key="comparison_chart_metric",
    )

    chart = chart_data.set_index("Vendor")[[selected_metric]]

    st.bar_chart(chart)
    
    profit_a = vendor_a["EstimatedProfitAfterFreight"]
    profit_b = vendor_b["EstimatedProfitAfterFreight"]

    if profit_a > profit_b:
        st.success(
            f"{vendor_a['VendorName']} has higher estimated profit "
            f"after freight by {profit_a - profit_b:,.2f}."
        )

    elif profit_b > profit_a:
        st.success(
            f"{vendor_b['VendorName']} has higher estimated profit "
            f"after freight by {profit_b - profit_a:,.2f}."
        )

    else:
        st.info(
            "Both vendors have equal estimated profit after freight."
        )