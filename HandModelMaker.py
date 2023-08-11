<<<<<<< HEAD
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

cols = df.columns
print(cols)

# Isolate class and feature columns
features = df.drop(cols[0], axis=1)
target = df[cols[0]]

X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.4, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f'Model accuracy: {accuracy*100}%')

with open('model.pkl', 'wb') as file:
    pickle.dump(model, file)
=======
import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import pickle


def build():
    # Establish a connection to the SQLite database
    conn = sqlite3.connect('data.db')

    # Write a SQL query to select all rows from the table
    query = 'SELECT * FROM static_data'

    # Use pandas to run the SQL query and store the result in a DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the connection to the database
    conn.close()

    print(df.describe(include='all'))

    df.drop('id', axis=1, inplace=True)

    # Remove NaNs
    df.dropna(inplace=True)

    cols = df.columns
    print(cols)

    # Isolate class and feature columns
    features = df.drop(cols[0], axis=1)
    target = df[cols[0]]

    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.4, random_state=42)

    model = MLPClassifier(hidden_layer_sizes=(8,), max_iter=10000)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print(f'Model accuracy: {accuracy*100}%')


    with open('model.pkl', 'wb') as file:
        pickle.dump(model, file)
>>>>>>> fbd6065 (Converted app to utilize flask instead of tkinter for interfacing)
