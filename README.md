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
- delivery metrics and customer state in the order fact;
- product-category labels and review scores in the item fact;
- documented Power BI measures and business rules.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Download and unzip the eight Olist CSV files into data/raw first.
python src/build_model.py
python -m pytest -q
```

The Kaggle download requires separate CLI installation and account authentication. If you already use the Kaggle CLI, the download command is:

```bash
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. Run commands from the repository root. Tests use small fixtures and do not need Kaggle credentials or downloaded data.

For `notebooks/key_visuals.ipynb`, install `pip install -r requirements-visuals.txt` in your notebook environment after building the reporting tables. Start the notebook with `notebooks/` as its working directory.

## Reporting outputs

| Output | Grain | What to inspect |
|---|---|---|
| `fact_orders.csv` | One order | Revenue, payments, review summaries, delivery dates and eligibility |
| `fact_order_items.csv` | One order item | Product/category and seller dimensions without payment/review join fan-out |
| `monthly_marketplace_kpis.csv` | One purchase month | Order counts, revenue, reviews and eligible-delivery rate |
| `seller_scorecard.csv` | One seller and state | Item economics, distinct orders and order-weighted reviews |

Business rules and denominator choices are documented in [KPI definitions](docs/KPI_DEFINITIONS.md). The Power BI file contains DAX definitions; a finished `.pbix` report is not included.

## Dashboard design

1. Executive marketplace overview
2. Delivery and fulfillment reliability
3. Seller scorecard
4. Product and category performance
5. Customer experience and reviews
6. Data quality and refresh controls

## Responsible interpretation

This is a historical marketplace sample. Review scores do not measure every customer experience, seller comparisons require sufficient order volume, and delivery performance varies by geography and product mix. The project separates operational facts from assumptions and avoids causal claims.


## Rebuild the reading edition

```bash
python -m pip install -r requirements-research.txt
python scripts/build_research_site.py
```

This renders saved notebook outputs without rerunning model training or external APIs. To refresh findings, run the analysis commands above first, update `reports/research-findings.md`, and rebuild.

<!-- research-edition:start -->
## Research edition

[Research report and final visual results](research/report.md) · [Browser-ready notebook catalogue](research/notebooks.html)

Fresh execution on 11 October 2026 using publisher Olist tables. The reporting model contains **99,441 order-level records**. Monthly revenue and on-time delivery rates use the exported monthly scorecard. Review-versus-delivery plots are associations within delivered and reviewed records, not evidence of a causal improvement. Customer and seller identifiers are not published in the reading edition.

| Measure | Value |
|---|---:|
| order rows | 99441 |
| monthly buckets | 25 |



The `research/` folder contains a professional static reading edition. The Pages workflow deploys it after GitHub Pages is enabled with **GitHub Actions** as the publishing source. Intended URL: `https://adeen1607.github.io/ecommerce-operations-analytics/`. Deployment status must be checked in Actions before treating that address as live.

<!-- research-edition:end -->
