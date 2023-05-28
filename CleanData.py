import pandas as pd


# Load Data
df = pd.read_csv('data.csv')

df.to_csv('olddata.csv', index=False)

print(df.describe(include='all'))

# Remove NaNs
df.dropna(inplace=True)

cols = df.columns
print(cols)

# Remove wrist columns if exist (easier than removing)
for col in cols:
    if "wrist" in col:
        df.drop(col, axis=1, inplace=True)

df.to_csv('data.csv', index=False)
