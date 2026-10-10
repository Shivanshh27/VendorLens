-- ============================================================
-- VendorIQ: Vendor Performance Analytics
-- Purpose: Create one consolidated analytical record per vendor
-- Database: SQLite
-- ============================================================


-- ============================================================
-- 1. PURCHASE AGGREGATION
-- Grain: One row per vendor
-- ============================================================

WITH purchase_summary AS (

    SELECT
        VendorNumber,

        COUNT(*) AS TotalPurchaseTransactions,

        SUM(Quantity) AS TotalPurchaseQuantity,

        ROUND(SUM(Dollars), 2) AS TotalPurchaseAmount,

        ROUND(AVG(Dollars), 2) AS AveragePurchaseTransactionValue

    FROM purchases

    GROUP BY VendorNumber
),


-- ============================================================
-- 2. SALES AGGREGATION
-- Grain: One row per vendor
-- ============================================================

sales_summary AS (

    SELECT
        VendorNumber,

        COUNT(*) AS TotalSalesTransactions,

        SUM(SalesQuantity) AS TotalSalesQuantity,

        ROUND(SUM(SalesDollars), 2) AS TotalSalesRevenue,

        ROUND(SUM(ExciseTax), 2) AS TotalExciseTax,

        ROUND(AVG(SalesDollars), 2) AS AverageSalesTransactionValue

    FROM sales

    GROUP BY VendorNumber
),


-- ============================================================
-- 3. PRODUCT COST AGGREGATION
-- Calculate estimated COGS using the product purchase price
-- ============================================================

sales_cost_summary AS (

    SELECT
        s.VendorNumber,

        ROUND(
            SUM(s.SalesQuantity * pp.PurchasePrice),
            2
        ) AS EstimatedCOGS

    FROM sales s

    JOIN purchase_prices pp
        ON s.Brand = pp.Brand

    GROUP BY s.VendorNumber
),


-- ============================================================
-- 4. FREIGHT AGGREGATION
-- Grain: One row per vendor
-- ============================================================

freight_summary AS (

    SELECT
        VendorNumber,

        COUNT(*) AS TotalInvoices,

        ROUND(SUM(Freight), 2) AS TotalFreightCost,

        ROUND(AVG(Freight), 2) AS AverageFreightPerInvoice

    FROM vendor_invoice

    GROUP BY VendorNumber
),


-- ============================================================
-- 5. INVENTORY AGGREGATION
-- Grain: One row per vendor
-- ============================================================

inventory_summary AS (

    WITH purchase_by_product AS (

        SELECT
            VendorNumber,
            Brand,
            SUM(Quantity) AS TotalUnitsPurchased
        FROM purchases
        GROUP BY VendorNumber, Brand

    ),

    sales_by_product AS (

        SELECT
            VendorNumber,
            Brand,
            SUM(SalesQuantity) AS TotalUnitsSold
        FROM sales
        GROUP BY VendorNumber, Brand

    )

    SELECT
        p.VendorNumber,
        SUM(p.TotalUnitsPurchased) AS TotalUnitsPurchased,
        SUM(COALESCE(s.TotalUnitsSold, 0)) AS TotalUnitsSold

    FROM purchase_by_product p

    LEFT JOIN sales_by_product s
        ON p.VendorNumber = s.VendorNumber
       AND p.Brand = s.Brand

    GROUP BY p.VendorNumber
),


-- ============================================================
-- 6. COMBINE VENDOR SUMMARIES
-- Each summary has at most one row per vendor
-- ============================================================

vendor_metrics AS (

    SELECT
        v.VendorNumber,
        v.VendorName,

        COALESCE(p.TotalPurchaseTransactions, 0)
            AS TotalPurchaseTransactions,

        COALESCE(p.TotalPurchaseQuantity, 0)
            AS TotalPurchaseQuantity,

        COALESCE(p.TotalPurchaseAmount, 0)
            AS TotalPurchaseAmount,

        COALESCE(s.TotalSalesTransactions, 0)
            AS TotalSalesTransactions,

        COALESCE(s.TotalSalesQuantity, 0)
            AS TotalSalesQuantity,

        COALESCE(s.TotalSalesRevenue, 0)
            AS TotalSalesRevenue,

        COALESCE(s.TotalExciseTax, 0)
            AS TotalExciseTax,

        COALESCE(c.EstimatedCOGS, 0)
            AS EstimatedCOGS,

        COALESCE(f.TotalInvoices, 0)
            AS TotalInvoices,

        COALESCE(f.TotalFreightCost, 0)
            AS TotalFreightCost,

        COALESCE(
            f.AverageFreightPerInvoice,
            0
        ) AS AverageFreightPerInvoice,

        COALESCE(i.TotalUnitsPurchased, 0)
            AS TotalUnitsPurchased,

        COALESCE(i.TotalUnitsSold, 0)
            AS TotalUnitsSold

    FROM vendors v

    LEFT JOIN purchase_summary p
        ON v.VendorNumber = p.VendorNumber

    LEFT JOIN sales_summary s
        ON v.VendorNumber = s.VendorNumber

    LEFT JOIN sales_cost_summary c
        ON v.VendorNumber = c.VendorNumber

    LEFT JOIN freight_summary f
        ON v.VendorNumber = f.VendorNumber

    LEFT JOIN inventory_summary i
        ON v.VendorNumber = i.VendorNumber
)


-- ============================================================
-- 7. FINAL VENDOR PERFORMANCE METRICS
-- ============================================================

SELECT
    VendorNumber,
    VendorName,

    TotalPurchaseTransactions,
    TotalPurchaseQuantity,
    TotalPurchaseAmount,

    TotalSalesTransactions,
    TotalSalesQuantity,
    TotalSalesRevenue,

    EstimatedCOGS,

    ROUND(
        TotalSalesRevenue - EstimatedCOGS,
        2
    ) AS GrossProfit,

    ROUND(
        100.0 * (TotalSalesRevenue - EstimatedCOGS)
        / NULLIF(TotalSalesRevenue, 0),
        2
    ) AS GrossProfitMarginPercent,

    TotalExciseTax,

    TotalInvoices,
    TotalFreightCost,
    AverageFreightPerInvoice,

    ROUND(
        TotalSalesRevenue
        - EstimatedCOGS
        - TotalFreightCost,
        2
    ) AS EstimatedProfitAfterFreight,

    ROUND(
        TotalUnitsPurchased - TotalUnitsSold,
        0
    ) AS EstimatedRemainingInventory,

    ROUND(
        1.0 * TotalSalesQuantity
        / NULLIF(TotalUnitsPurchased, 0),
        4
    ) AS SalesToPurchaseQuantityRatio

FROM vendor_metrics

ORDER BY EstimatedProfitAfterFreight DESC;