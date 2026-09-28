import pandas as pd
import pytest

from src.build_model import build_item_fact, build_order_fact


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
