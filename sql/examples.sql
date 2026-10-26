-- Example SQL for a user-level experiment table.
SELECT variant, COUNT(*) AS eligible_users,
       SUM(CASE WHEN purchase_completed THEN 1 ELSE 0 END) AS purchases,
       AVG(CASE WHEN purchase_completed THEN 1.0 ELSE 0.0 END) AS conversion_rate
FROM analysis_users
WHERE experiment_eligible = TRUE
GROUP BY variant;

SELECT variant,
       AVG(CASE WHEN purchase_completed THEN order_value ELSE 0 END) AS revenue_per_eligible_user
FROM analysis_users
WHERE experiment_eligible = TRUE
GROUP BY variant;
