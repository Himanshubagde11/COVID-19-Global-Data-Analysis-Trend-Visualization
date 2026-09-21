-- ==============================================================================
-- Global Aggregation and Longitudinal Trend Analysis
-- Author & Lead Data Engineer: Himanshu Bagde (@Himanshubagde11)
-- Dataset Curator: Himanshu Bagde | Source: Our World in Data / WHO
-- ==============================================================================

-- 1. Global Daily Cases Trend
SELECT 
    date,
    SUM(new_cases) AS global_daily_cases,
    SUM(total_cases) AS global_cumulative_cases
FROM daily_covid_stats
GROUP BY date
ORDER BY date ASC;

-- 2. Global Daily Deaths Trend
SELECT 
    date,
    SUM(new_deaths) AS global_daily_deaths,
    SUM(total_deaths) AS global_cumulative_deaths,
    CASE 
        WHEN SUM(total_cases) > 0 THEN ROUND((SUM(total_deaths) * 100.0) / SUM(total_cases), 4)
        ELSE 0 
    END AS global_case_fatality_rate
FROM daily_covid_stats
GROUP BY date
ORDER BY date ASC;

-- 8. Global 7-Day Rolling Cases Average (Computed via SQL Window Function)
WITH DailyGlobalCases AS (
    SELECT 
        date,
        SUM(new_cases) AS daily_cases
    FROM daily_covid_stats
    GROUP BY date
)
SELECT 
    date,
    daily_cases,
    ROUND(AVG(daily_cases) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_7day_global_cases
FROM DailyGlobalCases
ORDER BY date ASC;

-- 9. Global 7-Day Rolling Deaths Average (Window Function)
WITH DailyGlobalDeaths AS (
    SELECT 
        date,
        SUM(new_deaths) AS daily_deaths
    FROM daily_covid_stats
    GROUP BY date
)
SELECT 
    date,
    daily_deaths,
    ROUND(AVG(daily_deaths) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_7day_global_deaths
FROM DailyGlobalDeaths
ORDER BY date ASC;

-- 11. Monthly Aggregated Cases (Calendar Year and Month)
SELECT 
    SUBSTR(date, 1, 7) AS year_month,
    SUM(new_cases) AS monthly_new_cases,
    ROUND(AVG(new_cases), 2) AS daily_average_for_month,
    MAX(new_cases) AS peak_single_day_cases
FROM daily_covid_stats
GROUP BY SUBSTR(date, 1, 7)
ORDER BY year_month ASC;

-- 12. Monthly Aggregated Deaths
SELECT 
    SUBSTR(date, 1, 7) AS year_month,
    SUM(new_deaths) AS monthly_new_deaths,
    ROUND(AVG(new_deaths), 2) AS daily_average_for_month,
    MAX(new_deaths) AS peak_single_day_deaths
FROM daily_covid_stats
GROUP BY SUBSTR(date, 1, 7)
ORDER BY year_month ASC;
