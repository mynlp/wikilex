import sqlite3
from os import path

DB_PATH = r"{path}/db/lexicon.db".format(path=path.dirname(path.abspath(__file__)))
QUERIES_PATH = path.dirname(path.abspath(__file__)) + '/queries'


class Lexicon:

    def __init__(self):
        self.connection = sqlite3.connect(DB_PATH)

    def get_lexicon_mention(self, target_words=[]):
        template_name = 'get_mentions_urls'
        if not target_words:
            template_name = 'read_all_lexicon'
        with open('{path}/{name}.sql'.format(path=QUERIES_PATH, name=template_name), 'r') as query_file:
            query_template = query_file.read()
        cursor = self.connection.cursor()
        values = "'" + "','".join(target_words) + "'"
        query = query_template.format(target_words=values)
        lexicon = {}
        mention_urls_pairs = cursor.execute(query).fetchall()
        for mention, url in mention_urls_pairs:
            if mention not in lexicon.keys():
                lexicon.update({mention: []})
            lexicon[mention].append(url)
        return lexicon

    def insert_mentions_uris(self, lexicon):
        with open('{path}/insert_mention.sql'.format(path=QUERIES_PATH), 'r') as query_file:
            query = query_file.read()
        cursor = self.connection.cursor()
        if lexicon:
            for mention, uri, sentence in lexicon:
                cursor.execute(query, (mention, uri, sentence))

    def insert_categories_uri(self, uri, categories):
        with open('{path}/insert_category.sql'.format(path=QUERIES_PATH), 'r') as query_file:
            query = query_file.read()
        cursor = self.connection.cursor()
        if categories:
            for category in categories:
                cursor.execute(query, (uri, category))

    def insert_links_uri(self, source_uri, linked_uris):
        with open('{path}/insert_link.sql'.format(path=QUERIES_PATH), 'r') as query_file:
            query = query_file.read()
        cursor = self.connection.cursor()
        if linked_uris:
            for target_uri in linked_uris:
                cursor.execute(query, (source_uri, target_uri))
