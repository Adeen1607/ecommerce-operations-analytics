"""Build order, seller, and category reporting tables from Olist data."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "translation": "product_category_name_translation.csv",
}
DATE_COLUMNS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def load_tables(input_dir: Path) -> dict[str, pd.DataFrame]:
    tables = {}
    missing = []
    for name, filename in FILES.items():
        path = input_dir / filename
        if not path.exists():
            missing.append(filename)
        else:
            tables[name] = pd.read_csv(path)
    if missing:
        raise FileNotFoundError(f"Missing Olist files: {missing}")
    return tables


def build_order_fact(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = tables["orders"].copy()
    for column in DATE_COLUMNS:
        orders[column] = pd.to_datetime(orders[column], errors="coerce")

    item_summary = (
        tables["items"]
        .assign(
            item_value=lambda data: data["price"] + data["freight_value"],
        )
        .groupby("order_id")
        .agg(
            product_revenue=("price", "sum"),
            freight_value=("freight_value", "sum"),
            item_count=("order_item_id", "count"),
            seller_count=("seller_id", "nunique"),
        )
        .reset_index()
    )
    payment_summary = (
        tables["payments"]
        .groupby("order_id")
        .agg(
            payment_value=("payment_value", "sum"),
            payment_installments=("payment_installments", "max"),
            payment_types=("payment_type", "nunique"),
        )
        .reset_index()
    )
    review_summary = (
        tables["reviews"]
        .groupby("order_id")
        .agg(
            review_score=("review_score", "mean"),
            review_count=("review_id", "nunique"),
        )
        .reset_index()
    )
    customer = tables["customers"][
        ["customer_id", "customer_unique_id", "customer_city", "customer_state"]
    ]

    fact = (
        orders.merge(item_summary, on="order_id", how="left", validate="one_to_one")
        .merge(payment_summary, on="order_id", how="left", validate="one_to_one")
        .merge(review_summary, on="order_id", how="left", validate="one_to_one")
        .merge(customer, on="customer_id", how="left", validate="many_to_one")
    )
    fact["delivery_days"] = (
        fact["order_delivered_customer_date"] - fact["order_purchase_timestamp"]
    ).dt.total_seconds() / 86_400
    fact["delivery_variance_days"] = (
        fact["order_delivered_customer_date"]
        - fact["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86_400
    fact["on_time_delivery"] = fact["delivery_variance_days"].le(0)
    fact.loc[fact["order_delivered_customer_date"].isna(), "on_time_delivery"] = pd.NA
    fact["freight_share"] = fact["freight_value"] / fact["product_revenue"].where(
        fact["product_revenue"].ne(0)
    )
    fact["purchase_month"] = (
        fact["order_purchase_timestamp"].dt.to_period("M").astype("string")
    )
    return fact


def build_item_fact(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    items = tables["items"].copy()
    products = tables["products"].merge(
        tables["translation"],
        on="product_category_name",
        how="left",
        validate="many_to_one",
    )
    sellers = tables["sellers"][
        ["seller_id", "seller_city", "seller_state"]
    ]
    reviews = tables["reviews"].groupby("order_id", as_index=False).agg(
        review_score=("review_score", "mean")
    )

    fact = (
        items.merge(products, on="product_id", how="left", validate="many_to_one")
        .merge(sellers, on="seller_id", how="left", validate="many_to_one")
        .merge(reviews, on="order_id", how="left", validate="many_to_one")
    )
    fact["gross_item_value"] = fact["price"] + fact["freight_value"]
    return fact


def build_model(input_dir: Path, output_dir: Path) -> None:
    tables = load_tables(input_dir)
    order_fact = build_order_fact(tables)
    item_fact = build_item_fact(tables)
    output_dir.mkdir(parents=True, exist_ok=True)

    monthly = (
        order_fact.groupby("purchase_month", dropna=False)
        .agg(
            orders=("order_id", "nunique"),
            customers=("customer_unique_id", "nunique"),
            product_revenue=("product_revenue", "sum"),
            freight_value=("freight_value", "sum"),
            average_review_score=("review_score", "mean"),
            average_delivery_days=("delivery_days", "mean"),
            on_time_delivery_rate=("on_time_delivery", "mean"),
        )
        .reset_index()
    )
    seller = (
        item_fact.groupby(["seller_id", "seller_state"], dropna=False)
        .agg(
            orders=("order_id", "nunique"),
            product_revenue=("price", "sum"),
            freight_value=("freight_value", "sum"),
            average_review_score=("review_score", "mean"),
        )
        .reset_index()
        .sort_values("product_revenue", ascending=False)
    )

    order_fact.to_csv(output_dir / "fact_orders.csv", index=False)
    item_fact.to_csv(output_dir / "fact_order_items.csv", index=False)
    monthly.to_csv(output_dir / "monthly_marketplace_kpis.csv", index=False)
    seller.to_csv(output_dir / "seller_scorecard.csv", index=False)
    print(f"Reporting tables written to {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Olist BI reporting tables.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build_model(arguments.input_dir, arguments.output_dir)
