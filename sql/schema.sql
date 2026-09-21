-- ==============================================================================
-- COVID-19 Global Data Analysis & Trend Visualization
-- Normalized Relational Database Schema DDL
-- Compatible with SQLite and PostgreSQL
-- ==============================================================================

-- Drop tables in reverse dependency order if recreating
DROP TABLE IF EXISTS vaccination_stats;
DROP TABLE IF EXISTS daily_covid_stats;
DROP TABLE IF EXISTS population_stats;
DROP TABLE IF EXISTS countries;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS pipeline_metadata;

-- 0. Pipeline and Author Metadata Table
CREATE TABLE pipeline_metadata (
    metadata_id INTEGER PRIMARY KEY,
    project_name VARCHAR(150) NOT NULL,
    lead_data_engineer VARCHAR(100) NOT NULL,
    dataset_curator VARCHAR(100) NOT NULL,
    pipeline_version VARCHAR(20) NOT NULL,
    created_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_attribution TEXT NOT NULL
);

-- 1. Regions Lookup Table
CREATE TABLE regions (
    region_id INTEGER PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Countries Master Table
CREATE TABLE countries (
    country_id INTEGER PRIMARY KEY,
    iso_code VARCHAR(10),
    country_name VARCHAR(150) NOT NULL UNIQUE,
    region_id INTEGER,
    population BIGINT,
    population_density NUMERIC(10, 2),
    median_age NUMERIC(5, 2),
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

-- 3. Population and Demographic Stats Table
CREATE TABLE population_stats (
    country_id INTEGER PRIMARY KEY,
    population BIGINT,
    population_density NUMERIC(10, 2),
    median_age NUMERIC(5, 2),
    gdp_per_capita NUMERIC(12, 2),
    life_expectancy NUMERIC(5, 2),
    hospital_beds_per_thousand NUMERIC(6, 2),
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

-- 4. Daily COVID-19 Epidemiology Stats Table
CREATE TABLE daily_covid_stats (
    record_id INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL,
    date DATE NOT NULL,
    new_cases NUMERIC(12, 2) DEFAULT 0,
    total_cases NUMERIC(14, 2) DEFAULT 0,
    new_deaths NUMERIC(12, 2) DEFAULT 0,
    total_deaths NUMERIC(14, 2) DEFAULT 0,
    case_fatality_rate NUMERIC(6, 4) DEFAULT 0,
    cases_per_100k NUMERIC(10, 4) DEFAULT 0,
    deaths_per_100k NUMERIC(10, 4) DEFAULT 0,
    rolling_7day_cases NUMERIC(12, 2) DEFAULT 0,
    rolling_7day_deaths NUMERIC(12, 2) DEFAULT 0,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

-- 5. Daily Vaccination Stats Table
CREATE TABLE vaccination_stats (
    record_id INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_vaccinations NUMERIC(16, 2) DEFAULT 0,
    people_vaccinated NUMERIC(16, 2) DEFAULT 0,
    people_fully_vaccinated NUMERIC(16, 2) DEFAULT 0,
    new_vaccinations NUMERIC(14, 2) DEFAULT 0,
    vaccination_rate NUMERIC(6, 4) DEFAULT 0,
    fully_vaccinated_rate NUMERIC(6, 4) DEFAULT 0,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

-- ==============================================================================
-- Performance Optimization Indexes
-- ==============================================================================
CREATE INDEX idx_countries_region ON countries(region_id);
CREATE INDEX idx_countries_name ON countries(country_name);

CREATE INDEX idx_daily_country_id ON daily_covid_stats(country_id);
CREATE INDEX idx_daily_date ON daily_covid_stats(date);
CREATE INDEX idx_daily_country_date ON daily_covid_stats(country_id, date);

CREATE INDEX idx_vax_country_id ON vaccination_stats(country_id);
CREATE INDEX idx_vax_date ON vaccination_stats(date);
CREATE INDEX idx_vax_country_date ON vaccination_stats(country_id, date);
