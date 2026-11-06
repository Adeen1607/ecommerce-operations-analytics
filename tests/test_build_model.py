import pandas as pd
import pytest

from src.build_model import (
    FILES, build_item_fact, build_model, build_order_fact, build_seller_scorecard,
)


def sample_tables() -> dict[str, pd.DataFrame]:
    return {
        "orders": pd.DataFrame(
            {
                "order_id": ["order-1", "order-2"],
                "customer_id": ["customer-1", "customer-2"],
                "order_status": ["delivered", "shipped"],
                "order_purchase_timestamp": ["2018-01-01 10:00", "2018-01-03 09:00"],
                "order_approved_at": ["2018-01-01 11:00", "2018-01-03 10:00"],
                "order_delivered_carrier_date": ["2018-01-02", "2018-01-04"],
                "order_delivered_customer_date": ["2018-01-05", None],
                "order_estimated_delivery_date": ["2018-01-07", "2018-01-10"],
            }
        ),
        "items": pd.DataFrame(
            {
                "order_id": ["order-1", "order-1", "order-2"],
                "order_item_id": [1, 2, 1],
                "product_id": ["product-1", "product-2", "product-1"],
                "seller_id": ["seller-1", "seller-2", "seller-1"],
                "price": [100.0, 50.0, 80.0],
                "freight_value": [20.0, 5.0, 8.0],
            }
        ),
        "payments": pd.DataFrame(
            {
                "order_id": ["order-1", "order-1", "order-2"],
                "payment_type": ["credit_card", "voucher", "credit_card"],
                "payment_installments": [2, 1, 1],
                "payment_value": [150.0, 25.0, 88.0],
            }
        ),
        "reviews": pd.DataFrame(
            {
                "review_id": ["review-1", "review-2"],
                "order_id": ["order-1", "order-2"],
                "review_score": [5, 3],
            }
        ),
        "customers": pd.DataFrame(
            {
                "customer_id": ["customer-1", "customer-2"],
                "customer_unique_id": ["unique-1", "unique-2"],
                "customer_city": ["sao paulo", "curitiba"],
                "customer_state": ["SP", "PR"],
            }
        ),
        "products": pd.DataFrame(
            {
                "product_id": ["product-1", "product-2"],
                "product_category_name": ["beleza_saude", "livros"],
            }
        ),
        "sellers": pd.DataFrame(
            {
                "seller_id": ["seller-1", "seller-2"],
                "seller_city": ["campinas", "rio de janeiro"],
                "seller_state": ["SP", "RJ"],
            }
        ),
        "translation": pd.DataFrame(
            {
                "product_category_name": ["beleza_saude", "livros"],
                "product_category_name_english": ["health_beauty", "books"],
            }
        ),
    }


def test_order_fact_calculates_delivery_and_commercial_metrics() -> None:
    fact = build_order_fact(sample_tables()).set_index("order_id")

    delivered = fact.loc["order-1"]
    assert delivered["product_revenue"] == 150.0
    assert delivered["freight_value"] == 25.0
    assert delivered["item_count"] == 2
    assert delivered["seller_count"] == 2
    assert delivered["payment_value"] == 175.0
    assert delivered["payment_types"] == 2
    assert delivered["delivery_days"] == pytest.approx(3.583333, rel=1e-5)
    assert delivered["delivery_variance_days"] == -2.0
    assert bool(delivered["on_time_delivery"]) is True
    assert delivered["freight_share"] == pytest.approx(1 / 6)
    assert delivered["purchase_month"] == "2018-01"

    assert pd.isna(fact.loc["order-2", "on_time_delivery"])
    assert pd.isna(fact.loc["order-2", "delivery_days"])


def test_item_fact_preserves_item_grain_and_enriches_dimensions() -> None:
    fact = build_item_fact(sample_tables())

    assert len(fact) == 3
    assert fact[["order_id", "order_item_id"]].duplicated().sum() == 0

    first_item = fact.loc[
        (fact["order_id"] == "order-1") & (fact["order_item_id"] == 1)
    ].iloc[0]
    assert first_item["gross_item_value"] == 120.0
    assert first_item["product_category_name_english"] == "health_beauty"
    assert first_item["seller_state"] == "SP"
    assert first_item["review_score"] == 5


@pytest.mark.parametrize("missing_column", [
    "order_delivered_customer_date", "order_estimated_delivery_date"
])
def test_delivery_with_missing_date_is_unknown(missing_column: str) -> None:
    tables = sample_tables()
    tables["orders"].loc[0, missing_column] = None
    fact = build_order_fact(tables)

    assert str(fact["on_time_delivery"].dtype) == "boolean"
    assert pd.isna(fact.loc[0, "on_time_delivery"])
    assert pd.isna(fact.loc[0, "delivery_variance_days"])


def test_delivery_any_time_on_promised_date_is_on_time() -> None:
    tables = sample_tables()
    tables["orders"].loc[0, "order_delivered_customer_date"] = "2018-01-07 23:59:59"
    fact = build_order_fact(tables)

    assert fact.loc[0, "delivery_variance_days"] == 0
    assert bool(fact.loc[0, "on_time_delivery"]) is True


def test_seller_reviews_are_weighted_by_order_not_number_of_items() -> None:
    tables = sample_tables()
    # One seller has two items in a five-star order and one in a one-star order.
    tables["items"].loc[1, "seller_id"] = "seller-1"
    tables["reviews"].loc[1, "review_score"] = 1
    item_fact = build_item_fact(tables)
    seller = build_seller_scorecard(item_fact).set_index("seller_id").loc["seller-1"]

    assert seller["orders"] == 2
    assert seller["product_revenue"] == 230
    assert seller["freight_value"] == 33
    assert seller["reviewed_orders"] == 2
    assert seller["average_review_score"] == 3


def test_unreviewed_orders_do_not_lower_seller_review_average() -> None:
    tables = sample_tables()
    tables["reviews"] = tables["reviews"].iloc[[0]]
    seller = build_seller_scorecard(build_item_fact(tables))
    first = seller.set_index("seller_id").loc["seller-1"]

    assert first["orders"] == 2
    assert first["reviewed_orders"] == 1
    assert first["average_review_score"] == 5


def test_csv_pipeline_preserves_grain_and_eligible_delivery_rate(tmp_path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    for name, table in sample_tables().items():
        table.to_csv(raw / FILES[name], index=False)
    output = tmp_path / "processed"

    build_model(raw, output)

    assert {path.name for path in output.iterdir()} == {
        "fact_orders.csv", "fact_order_items.csv",
        "monthly_marketplace_kpis.csv", "seller_scorecard.csv",
    }
    orders = pd.read_csv(output / "fact_orders.csv")
    items = pd.read_csv(output / "fact_order_items.csv")
    monthly = pd.read_csv(output / "monthly_marketplace_kpis.csv")
    assert len(orders) == 2
    assert len(items) == 3
    assert orders["product_revenue"].sum() == 230
    assert monthly.loc[0, "on_time_delivery_rate"] == 1
    assert pd.isna(orders.loc[1, "on_time_delivery"])
