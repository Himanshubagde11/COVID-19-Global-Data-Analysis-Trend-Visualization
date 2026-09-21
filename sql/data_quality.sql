-- ==============================================================================
-- COVID-19 Data Quality and Integrity Auditing Queries
-- Author & Lead Data Engineer: Himanshu Bagde (@Himanshubagde11)
-- Dataset Curator: Himanshu Bagde | Source: Our World in Data / WHO
-- ==============================================================================

-- 1. Check for Duplicate Country-Date Records
SELECT 
    country_id,
    date,
    COUNT(*) AS record_count
FROM daily_covid_stats
GROUP BY country_id, date
HAVING COUNT(*) > 1;

-- 2. Check for Negative Numbers in Daily Flow Metrics
SELECT 
    c.country_name,
    d.date,
    d.new_cases,
    d.new_deaths
FROM daily_covid_stats d
JOIN countries c ON d.country_id = c.country_id
WHERE d.new_cases < 0 OR d.new_deaths < 0;

-- 3. Check for Orphaned Daily Records (No matching Country)
SELECT 
    d.record_id,
    d.country_id,
    d.date
FROM daily_covid_stats d
LEFT JOIN countries c ON d.country_id = c.country_id
WHERE c.country_id IS NULL;

-- 4. Check Non-Monotonic Total Cases Anomaly (where total cases drop)
WITH CaseProgression AS (
    SELECT 
        c.country_name,
        d.date,
        d.total_cases,
        LAG(d.total_cases, 1) OVER (PARTITION BY d.country_id ORDER BY d.date) AS prev_total_cases
    FROM daily_covid_stats d
    JOIN countries c ON d.country_id = c.country_id
)
SELECT 
    country_name,
    date,
    total_cases,
    prev_total_cases,
    (total_cases - prev_total_cases) AS reporting_drop
FROM CaseProgression
WHERE prev_total_cases IS NOT NULL 
  AND total_cases < prev_total_cases
ORDER BY reporting_drop ASC
LIMIT 50;

-- 5. Data Completeness Summary by Region
SELECT 
    COALESCE(r.region_name, 'Unknown') AS region,
    COUNT(DISTINCT c.country_id) AS countries_count,
    COUNT(d.record_id) AS total_daily_records,
    MIN(d.date) AS earliest_report,
    MAX(d.date) AS latest_report
FROM countries c
LEFT JOIN regions r ON c.region_id = r.region_id
LEFT JOIN daily_covid_stats d ON c.country_id = d.country_id
GROUP BY r.region_name
ORDER BY total_daily_records DESC;
