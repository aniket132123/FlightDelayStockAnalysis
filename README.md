# FlightDelayStockAnalysis
This project investigates whether **operational inefficiencies** (measured by flight delays) affect **stock market performance** for major U.S. airlines.

It integrates **Bureau of Transportation Statistics (BTS)** flight delay data with **Yahoo Finance** stock data, stores the results in a **PostgreSQL** database, and applies **Granger causality testing** to evaluate potential predictive relationships.

**Goal:** Determine if airlines with more delays tend to experience lower short-term stock returns.

---

## Data Sources

| Source                                        | Description                                   | Example Variables                                        |
| --------------------------------------------- | --------------------------------------------- | -------------------------------------------------------- |
| **Bureau of Transportation Statistics (BTS)** | Monthly U.S. domestic flight data (CSV files) | `FL_DATE`, `ARR_DELAY`, `CANCELLED`, `OP_UNIQUE_CARRIER` |
| **Yahoo Finance (yfinance)**                  | Daily stock data for major airlines           | `Close`, `Open`, `High`, `Low`, `Volume`                 |

---

## Tools & Technologies

| Category      | Tools                                  |
| ------------- | -------------------------------------- |
| Language      | Python 3                               |
| Data Handling | `pandas`, `numpy`                      |
| Visualization | `seaborn`, `matplotlib`                |
| Statistics    | `scipy`, `statsmodels`                 |
| Finance       | `yfinance`                             |
| Database      | `PostgreSQL`, `SQLAlchemy`, `psycopg2` |

---

## Methodology

### 1. Data Cleaning & Missing Value Analysis

* Combined monthly BTS CSVs into a single dataset.
* Visualized missing data with a heatmap.
* Used a **Chi-Square test** to assess whether missing delays are random across carriers.
* Filled missing `ARR_DELAY` values with each carrier’s mean delay.

### 2. Mapping Airlines to Stock Tickers

* Created a mapping of FAA carrier codes to Yahoo Finance tickers.
* Accounted for subsidiaries (e.g., `9E`, `MQ`, `OH` mapped to `AAL`).

### 3. Database Integration

* Stored the cleaned flight data to a **PostgreSQL** database named `flight_data`.

### 4. Stock Data Retrieval

* Downloaded daily stock price data (July 2024 – July 2025) for all mapped tickers.
* Calculated **daily stock returns** per airline.

### 5. Statistical Testing

* Verified **stationarity** using the Augmented Dickey-Fuller (ADF) test.
* Conducted **Granger causality tests** (lags 1–5) to determine if flight delays predict stock returns.
* Combined results across airlines using **Fisher’s method** to summarize significance.

---

## Outputs

**Missingness Check:**

```
Missingness might depend on carrier (not MCAR)
Missing data (%):  0.013376866954650669
```

**Causality Test Results (Per Lag):**

```
1  : 0.5712730644683146 SD:  0.2599717780664828
2  : 0.2200162647400005 SD:  0.3625967528452109
3  : 0.024627090899325303 SD:  0.3140350983941467
4  : 0.11168598652924376 SD:  0.3165748385485352
5  : 0.04019846768413254 SD:  0.27296217582133736
```

**Interpretation:**
Low p-values (< 0.05) suggest that increases in flight delays may precede declines in airline stock prices in the short term (3 - 5 days). This means that airline operational data can offer some **short-term predictive insights** into financial performance.

---

## How to Run

1. **Install dependencies**

   ```bash
   pip install pandas numpy matplotlib seaborn scipy statsmodels yfinance sqlalchemy psycopg2
   ```

2. **Start PostgreSQL** and create a database

   ```sql
   CREATE DATABASE flight_data;
   ```

3. **Update database credentials** in the script

   ```python
   engine = create_engine("postgresql+psycopg2://USERNAME:PASSWORD@localhost:5432/flight_data")
   ```

4. **Run the analysis**

   ```bash
   python analyze_flight_delays.py
   ```

---

### 6. Data Visualization (Tableau Dashboard)

To complement the Python analysis, an interactive Tableau dashboard was created to visualize the key findings.

**Dashboard Components:**

Sheet 1: Average Flight Delay per Airline

Sheet 2: Stock Returns Comparison

Sheet 3: Correlation Between Mean Delay and Stock Performance (dual-axis bar chart)

These visualizations make it easy to identify which airlines maintain consistent operational efficiency and whether that aligns with their stock performance.

**View the Dashboard:**
[View on Tableau Public]([https://public.tableau.com/views/FlightDelaysandStockReturns/Dashboard1](https://public.tableau.com/app/profile/aniket.singh2267/viz/FlightDelayStockReturnAnalysis/Dashboard1?publish=yes&showOnboarding=true))
