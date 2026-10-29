-- Cumulative repeat purchase windows; NOT exact-day D7 or D30 retention.
SELECT COUNT(*) AS first_orders,
    SUM(repeat_order_at IS NOT NULL AND
        julianday(repeat_order_at)-julianday(first_order_at) <= 7) AS repeated_within_7d,
    SUM(repeat_order_at IS NOT NULL AND
        julianday(repeat_order_at)-julianday(first_order_at) <= 30) AS repeated_within_30d,
    ROUND(100.0 * SUM(repeat_order_at IS NOT NULL AND
        julianday(repeat_order_at)-julianday(first_order_at) <= 7) / COUNT(*), 2) AS repeat_7d_pct,
    ROUND(100.0 * SUM(repeat_order_at IS NOT NULL AND
        julianday(repeat_order_at)-julianday(first_order_at) <= 30) / COUNT(*), 2) AS repeat_30d_pct
FROM user_funnel WHERE first_order_at IS NOT NULL;
