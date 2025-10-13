import sqlite3
import pandas as pd

DATA_PROCESSED = '../data/processed'

sections = [
    "Meal",
    "Insulin_bolus",
    "Insulin_infusion",
    "Glucose_concentration",
    "Fingerstick_glucose_concentration",
    "Priming_event",
    "Refill_event",
    "Sensor_inserted",
    "Sensor_stopped",
    "Audio_alerts",
    "Vibrate_alerts"
]

conn = sqlite3.connect(f'{DATA_PROCESSED}/cgm-db')
cur = conn.cursor()

for i in sections:
    df = pd.read_csv(f'{DATA_PROCESSED}/{i}.csv')
    df.to_sql(name=i.lower(), if_exists='replace', con=conn)

df_meal = pd.read_sql("SELECT * FROM meal LIMIT 5;", conn)
print(df_meal)