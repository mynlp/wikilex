import sqlite3
conn = sqlite3.connect(r"db/lexicon.db")
cursor = conn.cursor()
query = 'DROP TABLE IF EXISTS lexicon;'
cursor.execute(query)
query = 'DROP TABLE IF EXISTS mention_uris;'
cursor.execute(query)
query = 'DROP TABLE IF EXISTS entities;'
cursor.execute(query)
query = 'DROP TABLE IF EXISTS categories;'
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
