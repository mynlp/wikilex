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

    def insert_mentions_urls(self, lexicon):
        with open('{path}/insert_mentions.sql'.format(path=QUERIES_PATH), 'r') as query_file:
            query_template = query_file.read()
        list_lexicon = []
        for mention, urls in lexicon.items():
            for url in urls:
                list_lexicon.append((mention.replace("\'", "\'\'"), url.replace("\'", "\'\'")))
        values = ','.join([str(elem) for elem in list_lexicon])
        values = values.replace(r"'\\'", r'"\\"').replace(r"^\\'", r'"^\\"').replace(r"\'", r"''")\
            .replace(r'"\\"', r"'\\'").replace(r'"^\\"', r"^\\'").replace("(\"", "(\'").replace("\")", "\')")\
            .replace("\", ", "\', ").replace(", \"", ", \'").replace("\"", "\'\'")
        query = query_template.format(list_of_values=values)
        print(query)
        cursor = self.connection.cursor()
        cursor.execute(query)
