import sqlite3
import pandas as pd

if __name__=="__main__":
    db_connection = sqlite3.connect(r"pitchfork_album_reviews.db")
    db_cursor = db_connection.cursor()

    data = db_cursor.execute("SELECT * from reviews").fetchall()
    columns = names = list(map(lambda x: x[0], db_cursor.description))
    df = pd.DataFrame(data, columns=columns)

    df.to_csv('pitchfork_album_reviews.csv', index=False)
