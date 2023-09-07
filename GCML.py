import sqlite3
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import pickle


class MLManager:
    def __init__(self):
        self.modelFile = "static_model.pkl"
        self.model = pickle.load(open(self.modelFile, 'rb'))
        self.columns = ['thumb_cmc_dist', 'thumb_mcp_dist',
                        'thumb_dip_dist', 'thumb_tip_dist',
                        'index_cmc_dist', 'index_mcp_dist',
                        'index_dip_dist', 'index_tip_dist',
                        'middle_dip_dist', 'middle_tip_dist',
                        'middle_cmc_dist', 'middle_mcp_dist',
                        'ring_cmc_dist', 'ring_mcp_dist',
                        'ring_dip_dist', 'ring_tip_dist',
                        'pinky_cmc_dist', 'pinky_mcp_dist',
                        'pinky_dip_dist', 'pinky_tip_dist']

    def identify(self, data):
        df = pd.DataFrame(np.array(data).reshape(1, -1), columns=self.columns)
        prediction = self.model.predict(df)
        probability = self.model.predict_proba(df)
        if probability.max() < 0.3:
            prediction = "NONE"
        return prediction

    @staticmethod
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

        print(f'Model accuracy: {accuracy * 100}%')

        with open('static_model.pkl', 'wb') as file:
            pickle.dump(model, file)


if __name__ == "__main__":
    MLManager().build()
