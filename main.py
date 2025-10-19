import pandas as pd
from sqlalchemy import create_engine
import seaborn as sns
import matplotlib.pyplot as plt
import yfinance as yf


# Main goal: see if/how airline delays affect airline stock prices. Do airlines who tend to have more delays lose stock and lower
# prices?

# Taken from Bureau of Transportation Statistics
df = pd.read_csv("FlightDelayStockAnalysis/Airline_Delay_Cause.csv")

# check for missing data and volume of missing data
print("Missing data before:")
print(df.isnull().sum().sum())

# sns.heatmap(df.isnull(), cbar=False)
# plt.title("Missing Values Heatmap")
# plt.show()

# not a significant amount of missing data so drop NULL rows
df.dropna(inplace=True)
print("Missing data after:")
print(df.isnull().sum().sum())

# check data types
print(df.dtypes)

# remove duplicates
duplicates = df.duplicated().sum()
print("No duplicates") if duplicates == 0 else print("Duplicates found!")

# connect to database
engine = create_engine("postgresql+psycopg2://ds_user:mypassword@localhost:5432/flight_data")

df.to_sql(
    'flight_delays',
    engine,
    if_exists="replace",
    index=False
)

df_check = pd.read_sql("SELECT * FROM flight_delays LIMIT 5;", engine)

print(df_check)



