# E-commerce Operations Analytics

A business-intelligence case study built around marketplace orders, delivery performance, seller quality, freight cost, customer experience, and review outcomes.

## Business questions

- What drives late deliveries and low review scores?
- Which sellers and product categories create the most revenue and operational risk?
- How much of order value is consumed by freight?
- Where do cancellations and fulfillment delays concentrate?
- How do delivery promises compare with actual delivery time?

## Data source

This project uses the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), containing approximately 100,000 marketplace orders from 2016 through 2018. The files are downloaded directly from the publisher's Kaggle listing and are not redistributed here.

## Analytical model

The pipeline combines orders, order items, payments, reviews, customers, products, sellers, and category translations. It produces:

- order-level fulfillment and payment metrics;
- item-level product and seller performance;
- monthly marketplace KPIs;
- delivery reliability by state and seller;
- product-category revenue and review performance;
- documented Power BI measures and business rules.

## Setup

```bash
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/build_model.py
pytest
```

## Dashboard pages

1. Executive marketplace overview
2. Delivery and fulfillment reliability
3. Seller scorecard
4. Product and category performance
5. Customer experience and reviews
6. Data quality and refresh controls

## Responsible interpretation

This is a historical marketplace sample. Review scores do not measure every customer experience, seller comparisons require sufficient order volume, and delivery performance varies by geography and product mix. The project separates operational facts from assumptions and avoids causal claims.
