import csv
import sqlite3


class database:
    def __init__(self, name):
        # Establish the database connection and get a cursor
        self.conn = sqlite3.connect(name)
        self.cur = self.conn.cursor()

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

        self.cur.execute(query)
        self.conn.commit()

    def stop(self):
        self.conn.close()

    def getClasses(self):
        # Execute the SQL statement
        self.cur.execute("SELECT DISTINCT class FROM static_data")

        # Fetch all the rows
        rows = self.cur.fetchall()

        # Extract the unique values and return them
        return [row[0] for row in rows]

    def addEntry(self, data):
        if not len(data):
            return

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

        self.cur.execute(query, data)

        self.conn.commit()


if __name__ == "__main__":
    db = database("test.db")
    data = [10, 50, 35]
    db.addEntry(data)
    db.stop()
