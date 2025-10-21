import datetime
import pandas as pd
from sqlalchemy import create_engine
import seaborn as sns
import matplotlib.pyplot as plt
import yfinance as yf
import scipy.stats as stats
import os
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
import numpy as np
from scipy.stats import combine_pvalues

# Main goal: see if/how airline delays affect airline stock prices. Do airlines who tend to have more delays lose stock and have 
# lower prices?


df_csvs = []
# Taken from Bureau of Transportation Statistics
for file in os.scandir("FlightDelayStockAnalysis/months"):
    path = "FlightDelayStockAnalysis/months/" + file.name
    temp = pd.read_csv(path)
    df_csvs.append(temp)

df = pd.concat(df_csvs, ignore_index=True)
df = df.drop("YEAR", axis=1)
# Remove duplicate data
df = df.drop_duplicates()
duplicates = df.duplicated().sum()
if duplicates > 0:
    print("Duplicates: ", duplicates)

# Visually check for missing data and volume of missing data (close popup to proceed)
sns.heatmap(df.isnull(), cbar=False)
plt.title("Missing Values Heatmap")
plt.show()

# Create a column indicating whether ARR_DELAY is missing
df["MISSING_DELAY"] = df["ARR_DELAY"].isna()

# Create a contingency table between carrier and missing values
ct = pd.crosstab(df["OP_UNIQUE_CARRIER"], df["MISSING_DELAY"])

# Run the Chi-square test for independence
chi2, p_value, degrees_of_freedom, expected = stats.chi2_contingency(ct)

if p_value > 0.05:
    print("Missingness appears random with respect to carrier (MCAR assumption supported)")
else:
    print("Missingness might depend on carrier (not MCAR)")

missing_pct = (df["MISSING_DELAY"].sum().sum()/df["ARR_DELAY"].sum().sum()) * 100
print("Missing data (%): ", missing_pct)

# Not a significant amount of missing data (about 0.01%) but not MCAR so don't drop NULL rows
# instead fill missing data with mean of the missing airline's delays
df["ARR_DELAY"] = df.groupby("OP_UNIQUE_CARRIER")["ARR_DELAY"].transform(lambda x: x.fillna(x.mean()))
df.drop('MISSING_DELAY', axis=1, inplace=True)

# Connect to database
engine = create_engine("postgresql+psycopg2://ds_user:mypassword@localhost:5432/flight_data")

df.to_sql(
    'flight_delays',
    engine,
    if_exists="replace",
    index=False
)

# Change airline names to their tickers (account for subsidaries)
airline_to_ticker = {
    "9E": "DAL",     # Endeavor Air -> Delta subsidiary
    "AA": "AAL",     # American Airlines
    "AS": "ALK",     # Alaska Airlines
    "B6": "JBLU",    # JetBlue
    "C5": "UAL",     # CommuteAir -> United Express subsidary
    "DL": "DAL",     # Delta
    "F9": "ULCC",    # Frontier
    "G4": "ALGT",    # Allegiant
    "G7": "UAL",     # GoJet -> United Express subsidary
    "HA": "ALK",      # Hawaiian -> Alaskan subsidary
    "MQ": "AAL",     # Envoy  -> American subsidiary
    "OH": "AAL",     # PSA  -> American subsidiary
    "OO": "SKYW",    # SkyWest
    "PT": "AAL",     # Piedmont -> American subsidiary
    "QX": "ALK",     # Horizon -> Alaskan subsidiary
    "UA": "UAL",     # United
    "WN": "LUV",     # Southwest
    "YX": "AAL",     # Republic -> American subsidary
    "YV": "MESA"     # Mesa Airlines
}

# # Map airlines to their respective tickers
df['TICKER'] = df['OP_UNIQUE_CARRIER'].map(airline_to_ticker)

# Remove airlines with inaccesible ticker info
df = df.dropna(subset=['TICKER'])

# Download data from yahoo finance for stock data
start_date = datetime.datetime(2024, 7, 1)
end_date = datetime.datetime(2025, 7, 31)
df_finance = yf.download(list(airline_to_ticker.values()), start=start_date, end=end_date)

df['FL_DATE'] = pd.to_datetime(df['FL_DATE'].astype(str).str.strip())

df_daily = df.groupby(['FL_DATE', 'TICKER']).agg({
    'ARR_DELAY': 'mean', # average arrival delay per airline per day (in minutes delayed)
    'CANCELLED': 'sum' # total cancelled flights per airline per day
}).reset_index()

df_daily = df_daily.rename(columns={'FL_DATE' : 'Date', 'TICKER' : 'Ticker'})
df_finance = df_finance.reset_index()

# Create a list of DataFrames
df_list = []

# Can pick any column to extract tickers from but Close appears first
for ticker in df_finance['Close'].columns:
    temp = pd.DataFrame({
        'Date': df_finance['Date'],
        'Ticker': ticker,
        'Close': df_finance['Close'][ticker],
        'Open': df_finance['Open'][ticker],
        'High': df_finance['High'][ticker],
        'Low': df_finance['Low'][ticker],
        'Volume': df_finance['Volume'][ticker]
    })
    df_list.append(temp)

df_new_finance = pd.concat(df_list, ignore_index=True)

# Merge on inner to account for missing stock data
final_df = df_daily.merge(df_new_finance, how="inner", on=['Date', 'Ticker'])

# Compute daily stock returns
final_df['Returns'] = final_df.groupby('Ticker')['Close'].pct_change()
final_df = final_df.dropna(subset=['Returns'])
ticker_set = final_df['Ticker'].unique()

# Rows are levels of lag and columns are the ticker p-value results from GCT
p_values = np.empty((5,10))
t_count = 0

for ticker in ticker_set:
    df_temp = final_df[final_df['Ticker'] == ticker][['Date', 'ARR_DELAY', 'Returns']].dropna()
    df_temp = df_temp.set_index('Date')
    df_temp['ARR_DELAY_DIFF'] = df_temp['ARR_DELAY'].diff().dropna()

    # Check for stationarity using augmented Dickey-Fuller test
    p = 0
    for col in ['ARR_DELAY_DIFF', 'Returns']:
        p = adfuller(df_temp[col].dropna())[1]
        if p > 0.05:
            print("Column does not have stationarity!")
            print(col)
            break

    if p < 0.05:
        # Granger Causality test
        max_lag = 5
        test = grangercausalitytests(df_temp[['Returns', 'ARR_DELAY']], maxlag=max_lag)
        for i in range(1, max_lag+1):
            # Add p-values to the matrix
            p_values[i-1][t_count] = test[i][0]['ssr_ftest'][1]
        t_count+=1
    else:
        print("Cannot run Granger Causality as stationarity requirement isn't met")

# Use Fisher's method to combine p-values for each lag
for i in range(0,5):
    stat, combined_p = combine_pvalues(pvalues=p_values[i], method='fisher')
    std_dev = np.std(p_values[i])
    print(i+1, " :", combined_p, "SD: ", std_dev)



