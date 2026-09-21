-- ==============================================================================
-- COVID-19 Vaccination Progress & Epidemiological Interaction Queries
-- Author & Lead Data Engineer: Himanshu Bagde (@Himanshubagde11)
-- Dataset Curator: Himanshu Bagde | Source: Our World in Data / WHO
-- ==============================================================================

-- 10. Global and National Vaccination Coverage Status
WITH LatestVax AS (
    SELECT 
        country_id,
        MAX(date) AS max_vax_date
    FROM vaccination_stats
    WHERE people_vaccinated > 0
    GROUP BY country_id
)
SELECT 
    c.country_name,
    r.region_name,
    c.population,
    v.people_vaccinated,
    v.people_fully_vaccinated,
    ROUND((v.people_vaccinated * 100.0) / NULLIF(c.population, 0), 2) AS single_dose_coverage_pct,
    ROUND((v.people_fully_vaccinated * 100.0) / NULLIF(c.population, 0), 2) AS fully_vaccinated_pct,
    v.date AS latest_data_reported
FROM vaccination_stats v
JOIN LatestVax lv ON v.country_id = lv.country_id AND v.date = lv.max_vax_date
JOIN countries c ON v.country_id = c.country_id
LEFT JOIN regions r ON c.region_id = r.region_id
WHERE c.population >= 1000000
ORDER BY fully_vaccinated_pct DESC
LIMIT 30;

-- 16. Countries with Most Rapid Vaccination Rollout (Largest 30-day Increase in Doses Administered)
WITH MonthlyVaxProgression AS (
    SELECT 
        c.country_name,
        v.date,
        v.people_fully_vaccinated,
        LAG(v.people_fully_vaccinated, 30) OVER (
            PARTITION BY v.country_id ORDER BY v.date
        ) AS vax_30days_prior,
        c.population
    FROM vaccination_stats v
    JOIN countries c ON v.country_id = c.country_id
    WHERE c.population >= 5000000
)
SELECT 
    country_name,
    date AS peak_acceleration_date,
    (people_fully_vaccinated - vax_30days_prior) AS monthly_fully_vax_growth,
    ROUND(((people_fully_vaccinated - vax_30days_prior) * 100.0) / population, 2) AS population_pct_vaccinated_in_30days
FROM MonthlyVaxProgression
WHERE vax_30days_prior IS NOT NULL AND (people_fully_vaccinated - vax_30days_prior) > 0
ORDER BY monthly_fully_vax_growth DESC
LIMIT 25;

-- 17. Cases vs Vaccination Analysis (Pre-Vaccine vs Post-Vaccine Rollout Comparison)
-- Evaluates whether high vaccination coverage (>60%) correlates with lower death-to-case ratios
WITH LatestEpidemiology AS (
    SELECT 
        country_id,
        MAX(date) AS max_date
    FROM daily_covid_stats
    GROUP BY country_id
),
LatestVaccination AS (
    SELECT 
        country_id,
        MAX(date) AS max_vax_date
    FROM vaccination_stats
    WHERE people_fully_vaccinated > 0
    GROUP BY country_id
)
SELECT 
    CASE 
        WHEN (v.people_fully_vaccinated * 100.0) / NULLIF(c.population, 0) >= 70 THEN 'High Vax (>=70%)'
        WHEN (v.people_fully_vaccinated * 100.0) / NULLIF(c.population, 0) >= 40 THEN 'Medium Vax (40-69%)'
        ELSE 'Low Vax (<40%)'
    END AS vaccination_tier,
    COUNT(DISTINCT c.country_id) AS country_count,
    SUM(c.population) AS total_population,
    SUM(d.total_cases) AS total_cases,
    SUM(d.total_deaths) AS total_deaths,
    ROUND((SUM(d.total_deaths) * 100.0) / NULLIF(SUM(d.total_cases), 0), 4) AS group_case_fatality_rate,
    ROUND((SUM(d.total_cases) * 100000.0) / NULLIF(SUM(c.population), 0), 2) AS group_cases_per_100k,
    ROUND((SUM(d.total_deaths) * 100000.0) / NULLIF(SUM(c.population), 0), 2) AS group_deaths_per_100k
FROM daily_covid_stats d
JOIN LatestEpidemiology le ON d.country_id = le.country_id AND d.date = le.max_date
JOIN vaccination_stats v ON d.country_id = v.country_id
JOIN LatestVaccination lv ON v.country_id = lv.country_id AND v.date = lv.max_vax_date
JOIN countries c ON d.country_id = c.country_id
WHERE c.population >= 1000000
GROUP BY vaccination_tier
ORDER BY group_case_fatality_rate ASC;

-- 18. Deaths vs Vaccination Cross-Sectional Analysis by Country
WITH CountryLatestEpi AS (
    SELECT country_id, MAX(date) AS max_date FROM daily_covid_stats GROUP BY country_id
),
CountryLatestVax AS (
    SELECT country_id, MAX(date) AS max_date FROM vaccination_stats WHERE people_fully_vaccinated > 0 GROUP BY country_id
)
SELECT 
    c.country_name,
    r.region_name,
    c.population,
    ROUND((v.people_fully_vaccinated * 100.0) / NULLIF(c.population, 0), 2) AS fully_vaccinated_pct,
    ROUND((d.total_deaths * 100000.0) / NULLIF(c.population, 0), 2) AS deaths_per_100k,
    ROUND((d.total_deaths * 100.0) / NULLIF(d.total_cases, 0), 4) AS case_fatality_rate
FROM countries c
JOIN daily_covid_stats d ON c.country_id = d.country_id
JOIN CountryLatestEpi le ON d.country_id = le.country_id AND d.date = le.max_date
JOIN vaccination_stats v ON c.country_id = v.country_id
JOIN CountryLatestVax lv ON v.country_id = lv.country_id AND v.date = lv.max_date
LEFT JOIN regions r ON c.region_id = r.region_id
WHERE c.population >= 5000000
ORDER BY fully_vaccinated_pct DESC
LIMIT 30;
