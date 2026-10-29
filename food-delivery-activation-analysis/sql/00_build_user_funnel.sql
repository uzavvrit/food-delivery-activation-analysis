-- Source of truth: ordered first valid step within 7 days of signup.
-- Every timestamp is UTC and stored as YYYY-MM-DD HH:MM:SS.
DROP TABLE IF EXISTS user_funnel;
CREATE TABLE user_funnel AS
WITH address_step AS (
    SELECT u.*,
        (SELECT MIN(e.event_time) FROM events e
         WHERE e.user_id = u.user_id AND e.event_name = 'address_added'
           AND e.event_time > u.registered_at
           AND e.event_time <= datetime(u.registered_at, '+7 days')) AS address_at
    FROM users u
), restaurant_step AS (
    SELECT a.*,
        (SELECT MIN(e.event_time) FROM events e
         WHERE e.user_id = a.user_id AND e.event_name = 'restaurant_opened'
           AND e.event_time > a.address_at
           AND e.event_time <= datetime(a.registered_at, '+7 days')) AS restaurant_at
    FROM address_step a
), cart_step AS (
    SELECT r.*,
        (SELECT MIN(e.event_time) FROM events e
         WHERE e.user_id = r.user_id AND e.event_name = 'added_to_cart'
           AND e.event_time > r.restaurant_at
           AND e.event_time <= datetime(r.registered_at, '+7 days')) AS cart_at
    FROM restaurant_step r
), checkout_step AS (
    SELECT c.*,
        (SELECT MIN(e.event_time) FROM events e
         WHERE e.user_id = c.user_id AND e.event_name = 'checkout_started'
           AND e.event_time > c.cart_at
           AND e.event_time <= datetime(c.registered_at, '+7 days')) AS checkout_at
    FROM cart_step c
), completion_step AS (
    SELECT x.*,
        (SELECT MIN(e.event_time) FROM events e
         WHERE e.user_id = x.user_id AND e.event_name = 'order_completed'
           AND e.event_time > x.checkout_at
           AND e.event_time <= datetime(x.registered_at, '+7 days')) AS first_order_at,
        (SELECT MIN(e.event_time) FROM events e
         WHERE e.user_id = x.user_id AND e.event_name = 'payment_failed'
           AND e.event_time > x.checkout_at
           AND e.event_time <= datetime(x.registered_at, '+7 days')) AS payment_failure_at
    FROM checkout_step x
)
SELECT f.*,
    (SELECT MIN(e.event_time) FROM events e
     WHERE e.user_id = f.user_id AND e.event_name = 'repeat_order_completed'
       AND e.event_time > f.first_order_at
       AND e.event_time <= datetime(f.first_order_at, '+30 days')) AS repeat_order_at
FROM completion_step f;
CREATE UNIQUE INDEX IF NOT EXISTS idx_funnel_user ON user_funnel(user_id);
