# Data Source Attribution & Methodology

This project utilizes real-world open epidemiological and demographic data published by global health organizations and academic research institutions. All original data rights belong to their respective publishers.

---

## 1. Primary Datasets

### Our World in Data (OWID) COVID-19 Dataset
- **Publisher:** Our World in Data (University of Oxford / Global Change Data Lab)
- **Maintainers:** Edouard Mathieu, Hannah Ritchie, Lucas Rodés-Guirao, Cameron Appel, Charlie Giattino, Joe Hasell, Bobbie Macdonald, Saloni Dattani, Diana Beltekian, Esteban Ortiz-Ospina, and Max Roser.
- **Repository URL:** [https://github.com/owid/covid-19-data](https://github.com/owid/covid-19-data)
- **Raw Data Endpoint:** [https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv](https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv)
- **Access Timestamp:** September 2026 (Continuous mirror through official repository)
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Coverage:** Global coverage across 233+ sovereign countries and territories spanning 2020 through 2024. Contains 67 metrics covering confirmed cases, confirmed deaths, testing metrics, hospitalization/ICU occupancy, vaccine doses administered, and socioeconomic/demographic controls (population, GDP per capita, median age, hospital beds per thousand).

### Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)
- **Publisher:** Center for Systems Science and Engineering (CSSE) at Johns Hopkins University
- **Repository URL:** [https://github.com/CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19)
- **Reference Data Endpoints:**
  - `time_series_covid19_confirmed_US.csv`
  - `time_series_covid19_deaths_US.csv`
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Coverage:** County-level longitudinal time series across 3,340+ US counties and territories, totaling over 3.8M granular daily records.

### World Health Organization (WHO)
- **Publisher:** World Health Organization
- **Data Portal:** [https://covid19.who.int/data](https://covid19.who.int/data)
- **Reference URL:** [https://covid19.who.int/WHO-COVID-19-global-data.csv](https://covid19.who.int/WHO-COVID-19-global-data.csv)
- **Citation:** World Health Organization. Coronavirus (COVID-19) Dashboard.

---

## 2. Ingestion & Transformation Integrity

1. **Immutable Raw Storage:** Raw data ingested from upstream sources is preserved verbatim without modification in `data/raw/`.
2. **Deterministic Processing:** All transformations, country normalizations, and rolling averages are programmatically computed via `src/` modules with verifiable audit trails.
3. **No Fabrication:** All numerical outputs, summary tables, and visualizations represent verifiable mathematical calculations derived directly from the underlying datasets.
