import csv
import sqlite3


class database:
    def __init__(self, name):
        self.name = name

        # Establish the database connection and get a cursor
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()

        query = f'''CREATE TABLE IF NOT EXISTS static_data (
                                id INTEGER PRIMARY KEY,
                                class TEXT,
                                thumb_cmc_dist REAL,
                                thumb_mcp_dist REAL,
                                thumb_dip_dist REAL,
                                thumb_tip_dist REAL,
                                index_cmc_dist REAL,
                                index_mcp_dist REAL,
                                index_dip_dist REAL,
                                index_tip_dist REAL,
                                middle_dip_dist REAL,
                                middle_tip_dist REAL,
                                middle_cmc_dist REAL,
                                middle_mcp_dist REAL,
                                ring_cmc_dist REAL,
                                ring_mcp_dist REAL,
                                ring_dip_dist REAL,
                                ring_tip_dist REAL,
                                pinky_cmc_dist REAL,
                                pinky_mcp_dist REAL,
                                pinky_dip_dist REAL,
                                pinky_tip_dist REAL
                            );
                        '''

        cur.execute(query)
        conn.commit()
        conn.close()

    def get_all_table_names(self):
        # Establish the database connection and get a cursor
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()

        # Create and execute the SELECT query
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")

        # Fetch all results and close the connection
        tables = cur.fetchall()
        conn.close()

        # Extract table names and return as list of strings
        table_names = [table[0] for table in tables]
        return table_names

    def getClasses(self):
        # Establish the database connection and get a cursor
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()

        # Execute the SQL statement
        cur.execute("SELECT DISTINCT class FROM static_data")

        # Fetch all the rows
        rows = cur.fetchall()

        conn.commit()
        conn.close()

        # Extract the unique values and return them
        return [row for row in rows]

    def addEntry(self, data):
        if not len(data):
            return

        # Establish the database connection and get a cursor
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()

        values = "?"
        values += ", ?" * (len(data) - 1)

        query = f'''INSERT INTO static_data (
                    class,
                    thumb_cmc_dist,
                    thumb_mcp_dist,
                    thumb_dip_dist,
                    thumb_tip_dist,
                    index_cmc_dist,
                    index_mcp_dist,
                    index_dip_dist,
                    index_tip_dist,
                    middle_dip_dist,
                    middle_tip_dist,
                    middle_cmc_dist,
                    middle_mcp_dist,
                    ring_cmc_dist,
                    ring_mcp_dist,
                    ring_dip_dist,
                    ring_tip_dist,
                    pinky_cmc_dist,
                    pinky_mcp_dist,
                    pinky_dip_dist,
                    pinky_tip_dist
                    ) VALUES ({values}
                );
                '''

        cur.execute(query, data)

        conn.commit()
        conn.close()

    def removeClass(self, class_name):
        if not len(class_name):
            return

        # Establish the database connection and get a cursor
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()

        query = f'''
        delete from static_data where class is "{class_name}"
        '''

        cur.execute(query)

        conn.commit()
        conn.close()

    def getLast(self):
        pass

    def undo(self):
        # Establish the database connection and get a cursor
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()

        # Get the maximum ID value
        cur.execute("SELECT MAX(id) FROM static_data")
        max_id = cur.fetchone()[0]

        # If there's at least one row, delete the one with the maximum ID
        if max_id is not None:
            cur.execute(f"DELETE FROM static_data WHERE id is {max_id}")

        # Commit changes and close connection
        conn.commit()
        conn.close()

    def backup(self):
        # Establish the database connection and get a cursor
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()

        for table_name in self.get_all_table_names():
            query = f'''
            select * from {table_name}
            '''

            cur.execute(query)
            rows = cur.fetchall()

            # Write to CSV
            with open(f'{table_name}.csv', 'w', newline='') as f:
                writer = csv.writer(f)

                # Get and write column headers
                col_headers = [desc[0] for desc in cur.description][1:]
                writer.writerow(col_headers)

                # Write query results
                for row in rows:
                    writer.writerow(row[1:])

        conn.close()

    def load(self, csv_filename):
        # Read the CSV file
        with open(f"{csv_filename}.csv", 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = [row for row in reader]

        # Establish SQLite connection and create table
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()

        # Drop table if it exists
        cur.execute(f"DROP TABLE IF EXISTS {csv_filename}")

        # Create table query with ID as INTEGER PRIMARY KEY AUTOINCREMENT
        columns = ', '.join([f"{col} TEXT" for col in header])
        create_table_query = f"CREATE TABLE {csv_filename} (id INTEGER PRIMARY KEY, {columns})"

        cur.execute(create_table_query)

        # Insert CSV data into table
        insert_query = f"INSERT INTO {csv_filename} ({', '.join(header)}) VALUES ({', '.join(['?' for _ in header])})"

        cur.executemany(insert_query, rows)

        # Commit changes and close connection
        conn.commit()
        conn.close()


if __name__ == "__main__":
    db = database("data.db")
    name = input("Input name (without extension) of data to load, Input nothing to backup data: ")
    if name:
        db.load(name)
    else:
        db.backup()
