# KPI definitions and model grain

## Orders and item economics

`fact_orders` has one row per order. Items, payments and reviews are aggregated to order grain before joining, so multiple items or payment methods cannot multiply order revenue. The item fact retains one row per order item and carries product and seller attributes.

Product revenue is the sum of item prices; freight is separate. Neither metric represents marketplace profit, and the exports do not remove canceled orders from the commercial totals. Filter order status explicitly when using delivered-order revenue. Freight share is freight divided by product revenue, rather than freight divided by the freight-inclusive payment amount.

## Delivery reliability

- Delivery duration is elapsed time from purchase to actual customer delivery, in fractional days.
- Delivery variance compares the actual and promised **calendar dates**, in whole days. Any delivery on the promised date is on time, including delivery after midnight.
- `on_time_delivery` is a nullable Boolean. A missing actual date or promised date is **unknown**, not late.
- The on-time rate uses only orders with both dates available. Undelivered and unknown-promise orders are excluded from its denominator.
- The DAX late-order measure uses strict equality with false so blank values cannot be counted as late.

These measures describe observed deliveries in the historical dataset. They are not a live overdue-backlog measure.

## Review coverage and seller scorecards

Multiple reviews on one order are averaged to one order-level review score. The low-score rate is the share of **reviewed** orders whose average score is at most two. Unreviewed orders do not enter either side of that ratio.

Seller revenue and freight sum item values, but seller review averages weight each seller-order once. A five-star order with three items has the same review weight as a five-star order with one item. `reviewed_orders` exposes the coverage denominator alongside distinct total orders.

A review on an order containing several sellers is attached to every participating seller. It is an order-level customer experience signal, not evidence that a specific seller caused the score. Compare sellers only with adequate review coverage, and do not average `fact_order_items[review_score]` directly for an order-weighted score.
