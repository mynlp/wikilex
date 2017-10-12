from lexicon import Lexicon
from lib.contents_extractor import extract_anchor_links, get_category
from lib.wiki_xml_page_extractor import extract_page
from lib.content_cleaner import clean_title, format_as_uri
from multiprocessing import Pool
import argparse
import click

PROCESS_AMOUNT = 5


def extract_mention_links_categories(wiki_page):
    title, page_type, content = wiki_page
    if title and len(title) != 0:
        current_uri = format_as_uri(clean_title(title))
        categories = get_category(content)
        if page_type == 'redirect':
            target_uri = format_as_uri(content)
            links = [target_uri]
            # lexicon format:  mention, target_uri, source_uri, sentence
            lexicon = [(title, target_uri, current_uri, '#REDIRECT')]
        elif content:
            lexicon, links = extract_anchor_links(current_uri, content)
        return current_uri, lexicon, links, categories


def process_xml_wiki(xmlf):
    process_pool = Pool(processes=PROCESS_AMOUNT)
    lexicon_db = Lexicon()
    with click.progressbar(process_pool.map(extract_mention_links_categories, extract_page(xmlf)),
                           label='obtaining mentions and links') as mention_link_progress_bar:
        for source_uri, lexicon, links, categories_list in mention_link_progress_bar:
            lexicon_db.insert_categories_uri(source_uri, categories_list)
            lexicon_db.insert_links_uri(source_uri, links)
            lexicon_db.insert_mentions_uris(lexicon)


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--file',
                             dest='wiki_file_path',
                             default='./data/wiki.xml',
                             help='Sets the path to wikipedia dump xml file',
                             type=str)
    options = args_parser.parse_args()
    # segment the text in the input files
    print("Starting the Entity Extraction process...")
    process_xml_wiki(options.wiki_file_path)

if __name__ == '__main__':
    main()
