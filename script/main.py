import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
# from ..ui.plot_ui import launch_ui
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.plot_ui import launch_ui



path = r"C:\Users\vyasn\OneDrive\Desktop\Academics\Project_1\ECG_Visual\data\Raw_Data.csv"

# --- Step 1: Load data (no headers) ---
try:
    df = pd.read_csv(path, header=None)
except FileNotFoundError:
    print("File not found. Check your path.")
    exit()

# --- Step 2: Assign column names ---
column_names = ['timestamp', 'occupied'] + [f'ch_{i+1}' for i in range(40)]
df.columns = column_names

# --- Step 3: Drop 'occupied' column ---
df.drop(columns=['occupied'], inplace=True)

# --- Step 4: Display basic info ---
print(" First 5 rows:\n", df.head())
print("\n Shape of data:", df.shape)
print("\n Channel stats:\n", df.iloc[:, 1:].describe())

# --- Step 5: Normalize timestamps (~line 25 onwards) ---
def parse_timestamp(x):
    try:
        return datetime.strptime(str(x), '%Y-%m-%d %H:%M:%S:%f')  # full datetime
    except ValueError:
        try:
            return datetime.strptime(str(x), '%H:%M:%S:%f')  # time only
        except ValueError:
            return pd.NaT

df['timestamp'] = df['timestamp'].apply(parse_timestamp)

# --- Step 6: Drop rows with bad timestamps ---
df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)

# --- Step 7: Check sampling interval (~line 35) ---
time_diffs = df['timestamp'].diff().dropna().dt.total_seconds() * 1000  # in ms
print("\n Sampling interval stats (ms):")
print(time_diffs.describe())

# --- Step 8: Check for missing values in channels (~line 40) ---
nan_counts = df.isna().sum()
print("\n Missing values (if any):")
print(nan_counts[nan_counts > 0])

# Optional: Drop or fill missing values
df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)

# --- Step 9: Remove extreme spikes using IQR method ---
for col in df.columns[1:]:  # skip 'timestamp'
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    df[col] = np.where((df[col] < lower) | (df[col] > upper), np.nan, df[col])

# --- Fill gaps after removing outliers ---
df.interpolate(limit_direction='both', inplace=True)


if __name__ == "__main__":
    launch_ui(df)
