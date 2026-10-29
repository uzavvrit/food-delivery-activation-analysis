-- Diagnostic proxy, NOT proven cause: app, payment-provider and card data are absent.
SELECT platform, COUNT(*) AS checkout_users,
    SUM(payment_failure_at IS NOT NULL) AS users_with_payment_failure,
    ROUND(100.0 * SUM(payment_failure_at IS NOT NULL) / COUNT(*), 2) AS payment_failure_pct,
    SUM(first_order_at IS NOT NULL) AS completed_users,
    ROUND(100.0 * SUM(first_order_at IS NOT NULL) / COUNT(*), 2) AS checkout_success_pct,
    ROUND(100.0 * SUM(CASE WHEN payment_failure_at IS NOT NULL
                            AND first_order_at IS NOT NULL THEN 1 ELSE 0 END) /
          NULLIF(SUM(payment_failure_at IS NOT NULL),0), 2) AS recovered_after_failure_pct
FROM user_funnel WHERE checkout_at IS NOT NULL
GROUP BY platform ORDER BY platform;
