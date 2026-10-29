-- Distinct users are already guaranteed because user_funnel has one row per user.
WITH counts AS (
    SELECT 1 AS step, 'Signup' AS event, COUNT(*) AS users FROM user_funnel
    UNION ALL SELECT 2, 'Address added', COUNT(*) FROM user_funnel WHERE address_at IS NOT NULL
    UNION ALL SELECT 3, 'Restaurant opened', COUNT(*) FROM user_funnel WHERE restaurant_at IS NOT NULL
    UNION ALL SELECT 4, 'Added to cart', COUNT(*) FROM user_funnel WHERE cart_at IS NOT NULL
    UNION ALL SELECT 5, 'Checkout started', COUNT(*) FROM user_funnel WHERE checkout_at IS NOT NULL
    UNION ALL SELECT 6, 'First order', COUNT(*) FROM user_funnel WHERE first_order_at IS NOT NULL
)
SELECT step, event, users,
    ROUND(100.0 * users / FIRST_VALUE(users) OVER (ORDER BY step), 2) AS from_signup_pct,
    ROUND(100.0 * users / NULLIF(LAG(users) OVER (ORDER BY step),0), 2) AS from_previous_pct,
    LAG(users) OVER (ORDER BY step) - users AS lost_users
FROM counts ORDER BY step;
