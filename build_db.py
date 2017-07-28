import sqlite3
conn = sqlite3.connect(r"db/lexicon.db")
cursor = conn.cursor()
with open('queries/create_lexicon_table.sql', 'r') as query_file:
    query = query_file.read()
cursor.execute(query)
