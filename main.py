import datetime
import pandas as pd
from sqlalchemy import create_engine
import seaborn as sns
import matplotlib.pyplot as plt
import yfinance as yf
import scipy.stats as stats

# Main goal: see if/how airline delays affect airline stock prices. Do airlines who tend to have more delays lose stock and have 
# lower prices?

# Taken from Bureau of Transportation Statistics
df = pd.read_csv("FlightDelayStockAnalysis/July.csv")

# Remove duplicate data
df = df.drop_duplicates()
duplicates = df.duplicated().sum()
if duplicates > 0:
    print("Duplicates: ", duplicates)

# Visually check for missing data and volume of missing data
sns.heatmap(df.isnull(), cbar=False)
plt.title("Missing Values Heatmap")
plt.show()

# Create a column indicating whether ARR_DELAY is missing
df["MISSING_DELAY"] = df["ARR_DELAY"].isna()

# Create a contingency table between carrier and missing values
ct = pd.crosstab(df["OP_UNIQUE_CARRIER"], df["MISSING_DELAY"])

# Run the chi-square test for independence
chi2, p_value, degrees_of_freedom, expected = stats.chi2_contingency(ct)

if p_value > 0.05:
    print("Missingness appears random with respect to carrier (MCAR assumption supported)")
else:
    print("Missingness might depend on carrier (not MCAR)")
missing_pct = (df["MISSING_DELAY"].sum().sum()/df["ARR_DELAY"].sum().sum()) * 100
print("Missing data (%): ", missing_pct)
# Not a significant amount of missing data (about 0.01%) and MCAR so just drop NULL rows
df.dropna(inplace=True)
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
start_date = datetime.datetime(2025, 7, 1)
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

print(final_df)

