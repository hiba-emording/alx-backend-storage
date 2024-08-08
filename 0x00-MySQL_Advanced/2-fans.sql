-- Calculates the total number of fans for each origin in the `metal_bands` table,
-- ordering the results by the number of fans in descending order.
SELECT origin, SUM(fans) AS nb_fans
    FROM metal_bands
    GROUP BY origin
    ORDER BY nb_fans DESC;
