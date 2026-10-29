-- Compare segment behavior within the same funnel population.
SELECT 'platform' AS segment_type, platform AS segment, COUNT(*) AS signups,
    SUM(checkout_at IS NOT NULL) AS checkouts,
    SUM(first_order_at IS NOT NULL) AS first_orders,
    ROUND(100.0 * SUM(first_order_at IS NOT NULL) / COUNT(*), 2) AS signup_to_order_pct,
    ROUND(100.0 * SUM(first_order_at IS NOT NULL) /
          NULLIF(SUM(checkout_at IS NOT NULL), 0), 2) AS checkout_to_order_pct
FROM user_funnel GROUP BY platform
UNION ALL
SELECT 'channel', channel, COUNT(*),
    SUM(checkout_at IS NOT NULL), SUM(first_order_at IS NOT NULL),
    ROUND(100.0 * SUM(first_order_at IS NOT NULL) / COUNT(*), 2),
    ROUND(100.0 * SUM(first_order_at IS NOT NULL) /
          NULLIF(SUM(checkout_at IS NOT NULL), 0), 2)
FROM user_funnel GROUP BY channel
ORDER BY segment_type, segment;
