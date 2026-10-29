-- Every issue should have a count of zero. No silent dropping of bad rows.
SELECT 'duplicate_users' AS issue, COUNT(*) AS n FROM (
    SELECT user_id FROM users GROUP BY user_id HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'duplicate_event_ids', COUNT(*) FROM (
    SELECT event_id FROM events GROUP BY event_id HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'orphan_events', COUNT(*) FROM events e LEFT JOIN users u USING(user_id)
WHERE u.user_id IS NULL
UNION ALL
SELECT 'unexpected_events', COUNT(*) FROM events
WHERE event_name NOT IN ('signup','address_added','restaurant_opened','added_to_cart',
                         'checkout_started','payment_failed','order_completed','repeat_order_completed')
UNION ALL
SELECT 'missing_signup_events', COUNT(*) FROM users u
WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.user_id=u.user_id AND e.event_name='signup'
                  AND e.event_time=u.registered_at)
UNION ALL
SELECT 'events_before_registration', COUNT(*) FROM events e
JOIN users u USING (user_id) WHERE e.event_time < u.registered_at;
