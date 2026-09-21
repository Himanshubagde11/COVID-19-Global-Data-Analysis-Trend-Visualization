-- ==============================================================================
-- Advanced SQL Analytics: CTEs, Window Functions, Growth Rates & Wave Analysis
-- Author & Lead Data Engineer: Himanshu Bagde (@Himanshubagde11)
-- Dataset Curator: Himanshu Bagde | Source: Our World in Data / WHO
-- ==============================================================================

-- 15. Month-over-Month (MoM) Global Case & Death Growth Rate
WITH MonthlyAggregates AS (
    SELECT 
        SUBSTR(date, 1, 7) AS year_month,
        SUM(new_cases) AS total_cases,
        SUM(new_deaths) AS total_deaths
    FROM daily_covid_stats
    GROUP BY SUBSTR(date, 1, 7)
),
MonthlyGrowthCalculations AS (
    SELECT 
        year_month,
        total_cases,
        total_deaths,
        LAG(total_cases, 1) OVER (ORDER BY year_month) AS prior_month_cases,
        LAG(total_deaths, 1) OVER (ORDER BY year_month) AS prior_month_deaths
    FROM MonthlyAggregates
)
SELECT 
    year_month,
    total_cases,
    prior_month_cases,
    ROUND(
        CASE 
            WHEN prior_month_cases > 0 THEN ((total_cases - prior_month_cases) * 100.0) / prior_month_cases
            ELSE NULL 
        END, 2
    ) AS mom_cases_growth_pct,
    total_deaths,
    prior_month_deaths,
    ROUND(
        CASE 
            WHEN prior_month_deaths > 0 THEN ((total_deaths - prior_month_deaths) * 100.0) / prior_month_deaths
            ELSE NULL 
        END, 2
    ) AS mom_deaths_growth_pct
FROM MonthlyGrowthCalculations
ORDER BY year_month ASC;

-- Epidemiological Peak & Wave Inflection Detection using Window Smoothing
-- Identifies localized peaks where 7-day average was strictly greater than 14 days before and after
WITH CountrySmoothedTrends AS (
    SELECT 
        c.country_name,
        d.date,
        d.new_cases,
        ROUND(AVG(d.new_cases) OVER (
            PARTITION BY d.country_id ORDER BY d.date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2) AS cases_7d_avg,
        ROUND(AVG(d.new_cases) OVER (
            PARTITION BY d.country_id ORDER BY d.date 
            ROWS BETWEEN 20 PRECEDING AND 7 PRECEDING
        ), 2) AS prior_14d_avg,
        ROUND(AVG(d.new_cases) OVER (
            PARTITION BY d.country_id ORDER BY d.date 
            ROWS BETWEEN 1 FOLLOWING AND 14 FOLLOWING
        ), 2) AS post_14d_avg
    FROM daily_covid_stats d
    JOIN countries c ON d.country_id = c.country_id
    WHERE c.country_name IN ('United States', 'India', 'United Kingdom', 'Brazil', 'Germany')
)
SELECT 
    country_name,
    date AS wave_peak_date,
    cases_7d_avg AS peak_7day_average_cases,
    prior_14d_avg AS preceding_velocity,
    post_14d_avg AS succeeding_velocity,
    ROUND(cases_7d_avg - prior_14d_avg, 2) AS surge_intensity
FROM CountrySmoothedTrends
WHERE cases_7d_avg > 5000 
  AND cases_7d_avg > prior_14d_avg * 1.4
  AND cases_7d_avg > post_14d_avg * 1.2
ORDER BY country_name, wave_peak_date ASC;

-- Cumulative Trajectory Comparison: Days from 100th Confirmed Case
WITH CountryInitialMilestone AS (
    SELECT 
        country_id,
        MIN(date) AS day_zero_date
    FROM daily_covid_stats
    WHERE total_cases >= 100
    GROUP BY country_id
),
NormalizedTrajectories AS (
    SELECT 
        c.country_name,
        d.date,
        (JULIANDAY(d.date) - JULIANDAY(m.day_zero_date)) AS days_since_100_cases,
        d.total_cases,
        d.total_deaths
    FROM daily_covid_stats d
    JOIN CountryInitialMilestone m ON d.country_id = m.country_id
    JOIN countries c ON d.country_id = c.country_id
    WHERE d.date >= m.day_zero_date
      AND c.country_name IN ('United States', 'India', 'United Kingdom', 'Germany', 'Brazil', 'Italy')
)
SELECT 
    country_name,
    CAST(days_since_100_cases AS INT) AS days_since_outbreak_start,
    total_cases,
    total_deaths
FROM NormalizedTrajectories
WHERE days_since_100_cases IN (30, 60, 90, 180, 365, 730)
ORDER BY days_since_100_cases ASC, total_cases DESC;
