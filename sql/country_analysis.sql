-- ==============================================================================
-- Country and Regional Comparative Analytical Queries
-- ==============================================================================

-- 3. Country with Highest Cumulative Cases (Most Recent Reported Observation)
WITH LatestCountryCases AS (
    SELECT 
        country_id,
        MAX(date) AS max_date
    FROM daily_covid_stats
    GROUP BY country_id
)
SELECT 
    c.country_name,
    c.iso_code,
    r.region_name,
    d.total_cases,
    d.total_deaths,
    c.population
FROM daily_covid_stats d
JOIN LatestCountryCases l ON d.country_id = l.country_id AND d.date = l.max_date
JOIN countries c ON d.country_id = c.country_id
LEFT JOIN regions r ON c.region_id = r.region_id
ORDER BY d.total_cases DESC
LIMIT 20;

-- 4. Country with Highest Deaths
WITH LatestCountryDeaths AS (
    SELECT 
        country_id,
        MAX(date) AS max_date
    FROM daily_covid_stats
    GROUP BY country_id
)
SELECT 
    c.country_name,
    c.iso_code,
    r.region_name,
    d.total_deaths,
    d.total_cases,
    c.population,
    ROUND((d.total_deaths * 100.0) / NULLIF(d.total_cases, 0), 4) AS cfr_percentage
FROM daily_covid_stats d
JOIN LatestCountryDeaths l ON d.country_id = l.country_id AND d.date = l.max_date
JOIN countries c ON d.country_id = c.country_id
LEFT JOIN regions r ON c.region_id = r.region_id
ORDER BY d.total_deaths DESC
LIMIT 20;

-- 5. Countries with Highest Case Fatality Rate (CFR) (Filtered for statistical relevance: total_cases >= 50,000)
WITH LatestStats AS (
    SELECT 
        country_id,
        MAX(date) AS max_date
    FROM daily_covid_stats
    GROUP BY country_id
)
SELECT 
    c.country_name,
    r.region_name,
    d.total_cases,
    d.total_deaths,
    ROUND((d.total_deaths * 100.0) / NULLIF(d.total_cases, 0), 4) AS case_fatality_rate
FROM daily_covid_stats d
JOIN LatestStats l ON d.country_id = l.country_id AND d.date = l.max_date
JOIN countries c ON d.country_id = c.country_id
LEFT JOIN regions r ON c.region_id = r.region_id
WHERE d.total_cases >= 50000
ORDER BY case_fatality_rate DESC
LIMIT 25;

-- 6. Countries with Highest Cases per 100,000 Population (Min population: 500,000)
WITH LatestStats AS (
    SELECT 
        country_id,
        MAX(date) AS max_date
    FROM daily_covid_stats
    GROUP BY country_id
)
SELECT 
    c.country_name,
    r.region_name,
    c.population,
    d.total_cases,
    ROUND((d.total_cases * 100000.0) / NULLIF(c.population, 0), 2) AS cases_per_100k
FROM daily_covid_stats d
JOIN LatestStats l ON d.country_id = l.country_id AND d.date = l.max_date
JOIN countries c ON d.country_id = c.country_id
LEFT JOIN regions r ON c.region_id = r.region_id
WHERE c.population >= 500000
ORDER BY cases_per_100k DESC
LIMIT 25;

-- 7. Countries with Highest Deaths per 100,000 Population (Min population: 500,000)
WITH LatestStats AS (
    SELECT 
        country_id,
        MAX(date) AS max_date
    FROM daily_covid_stats
    GROUP BY country_id
)
SELECT 
    c.country_name,
    r.region_name,
    c.population,
    d.total_deaths,
    ROUND((d.total_deaths * 100000.0) / NULLIF(c.population, 0), 2) AS deaths_per_100k
FROM daily_covid_stats d
JOIN LatestStats l ON d.country_id = l.country_id AND d.date = l.max_date
JOIN countries c ON d.country_id = c.country_id
LEFT JOIN regions r ON c.region_id = r.region_id
WHERE c.population >= 500000
ORDER BY deaths_per_100k DESC
LIMIT 25;

-- 13. Country Global Burden Ranking using DENSE_RANK()
WITH LatestStats AS (
    SELECT 
        country_id,
        MAX(date) AS max_date
    FROM daily_covid_stats
    GROUP BY country_id
)
SELECT 
    c.country_name,
    d.total_cases,
    d.total_deaths,
    DENSE_RANK() OVER (ORDER BY d.total_cases DESC) AS case_rank,
    DENSE_RANK() OVER (ORDER BY d.total_deaths DESC) AS death_rank,
    DENSE_RANK() OVER (ORDER BY (d.total_cases * 100000.0) / NULLIF(c.population, 0) DESC) AS case_per_capita_rank,
    DENSE_RANK() OVER (ORDER BY (d.total_deaths * 100000.0) / NULLIF(c.population, 0) DESC) AS death_per_capita_rank
FROM daily_covid_stats d
JOIN LatestStats l ON d.country_id = l.country_id AND d.date = l.max_date
JOIN countries c ON d.country_id = c.country_id
WHERE c.population >= 1000000
ORDER BY case_rank ASC
LIMIT 30;

-- 14. Regional Ranking by Total Burden and Per-Capita Impact
WITH LatestStats AS (
    SELECT 
        country_id,
        MAX(date) AS max_date
    FROM daily_covid_stats
    GROUP BY country_id
)
SELECT 
    COALESCE(r.region_name, 'Unassigned') AS region,
    COUNT(DISTINCT c.country_id) AS sovereign_states,
    SUM(c.population) AS total_regional_population,
    SUM(d.total_cases) AS total_regional_cases,
    SUM(d.total_deaths) AS total_regional_deaths,
    ROUND((SUM(d.total_deaths) * 100.0) / NULLIF(SUM(d.total_cases), 0), 4) AS regional_cfr,
    ROUND((SUM(d.total_cases) * 100000.0) / NULLIF(SUM(c.population), 0), 2) AS regional_cases_per_100k,
    ROUND((SUM(d.total_deaths) * 100000.0) / NULLIF(SUM(c.population), 0), 2) AS regional_deaths_per_100k,
    RANK() OVER (ORDER BY SUM(d.total_cases) DESC) AS regional_case_rank,
    RANK() OVER (ORDER BY SUM(d.total_deaths) DESC) AS regional_death_rank
FROM daily_covid_stats d
JOIN LatestStats l ON d.country_id = l.country_id AND d.date = l.max_date
JOIN countries c ON d.country_id = c.country_id
LEFT JOIN regions r ON c.region_id = r.region_id
GROUP BY r.region_name
ORDER BY total_regional_cases DESC;
