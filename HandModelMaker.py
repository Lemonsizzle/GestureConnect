import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pickle

# Load Data
df = pd.read_csv('data.csv')
print(df.describe(include='all'))

# Remove NaNs
df.dropna(inplace=True)

# Remove "thumbs up" for now because it's just ruining rock classification
df = df[~df.apply(lambda row: row.astype(str).str.contains('tu').any(), axis=1)]

cols = df.columns
print(cols)

# Class and wrist coordinates aren't factors
features = df.drop(cols[0:4], axis=1)
target = df[cols[0]]

X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.4, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f'Model accuracy: {accuracy*100}%')

with open('model.pkl', 'wb') as file:
    pickle.dump(model, file)
