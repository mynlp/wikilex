import sqlite3
conn = sqlite3.connect(r"db/lexicon.db")
cursor = conn.cursor()
query = 'drop table mention_uris;'
cursor.execute(query)
query = 'drop table entities;'
cursor.execute(query)
query = 'drop table categories;'
cursor.execute(query)
with open('queries/create_mention_uris_table.sql', 'r') as query_file:
    query = query_file.read()
cursor.execute(query)
with open('queries/create_categories_table.sql', 'r') as query_file:
    query = query_file.read()
cursor.execute(query)
with open('queries/create_entities_table.sql', 'r') as query_file:
    query = query_file.read()
cursor.execute(query)
