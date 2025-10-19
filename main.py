import datetime
import pandas as pd
from sqlalchemy import create_engine, text
import seaborn as sns
import matplotlib.pyplot as plt
import yfinance as yf


# Main goal: see if/how airline delays affect airline stock prices. Do airlines who tend to have more delays lose stock and have 
# lower prices?

# Taken from Bureau of Transportation Statistics
df = pd.read_csv("FlightDelayStockAnalysis/Airline_Delay_Cause.csv")

# check for missing data and volume of missing data
# print("Missing data before:")
# print(df.isnull().sum().sum())

# sns.heatmap(df.isnull(), cbar=False)
# plt.title("Missing Values Heatmap")
# plt.show()

# not a significant amount of missing data so drop NULL rows
df.dropna(inplace=True)
# print("Missing data after:")
# print(df.isnull().sum().sum())

# check data types
# print(df.dtypes)

# remove duplicates
duplicates = df.duplicated().sum()
# print("No duplicates") if duplicates == 0 else print("Duplicates found!")

# connect to database
engine = create_engine("postgresql+psycopg2://ds_user:mypassword@localhost:5432/flight_data")

df.to_sql(
    'flight_delays',
    engine,
    if_exists="replace",
    index=False
)

# Get all carriers
# carriers = pd.read_sql("SELECT DISTINCT carrier_name FROM flight_delays;", engine)
# print(carriers)

# Change airline names to their tickers
airline_to_ticker = {
    "United Air Lines Network": "UAL",
    "CommuteAir LLC": "UAL",
    "GoJet Airlines LLC": "UAL",
    "Horizon Air": "ALK",
    "Envoy Air": "AAL",
    "PSA Airlines Inc.": "AAL",
    "Piedmont Airlines": "AAL",
    "Endeavor Air Inc.": "DAL",
    "Air Wisconsin Airlines Corp": "UAL",
    "Hawaiian Airlines Network": "ALK",
    "Alaska Airlines Network": "ALK",
    "SkyWest Airlines Inc.": "SKYW",
    "Mesa Airlines Inc.": "MESA",
    "Frontier Airlines": "ULCC",
    "American Airlines Network": "AAL",
    "Delta Air Lines Network": "DAL",
    "Southwest Airlines": "LUV",
    "JetBlue Airways": "JBLU",
    "Allegiant Air": "ALGT"
}

# Map airlines to their respective tickers
df['ticker'] = df['carrier_name'].map(airline_to_ticker)

# Remove airlines with inaccesible ticker info
df = df.dropna(subset=['ticker'])

# Download data from yahoo finance for stock data
start_date = datetime.datetime(2024, 7, 1)
end_date = datetime.datetime(2025, 7, 31)
data = yf.download(list(airline_to_ticker.values()), start=start_date, end=end_date)
print(data.head())

