# TODO: good example: http://www.heatonresearch.com/2017/03/03/python-basic-wikipedia-parsing.html
from lxml.etree import iterparse
from lexicon import Lexicon
import re
import argparse


def extract_page(xml_file):
    iterator = iterparse(xml_file)
    current_xml_tag = next(iterator)
    title = ''
    while current_xml_tag:
        if current_xml_tag[0] == 'end':
            if current_xml_tag[1].tag.endswith("title"):
                title = current_xml_tag[1].text
            elif current_xml_tag[1].tag.endswith("redirect"):
                redirect = current_xml_tag[1].attrib['title']
                if redirect:
                    mention = clean_title(title)
                    yield (mention, 'redirect', redirect)
            elif current_xml_tag[1].tag.endswith("text"):
                yield (title, 'text', current_xml_tag[1].text)
                title = ''
        current_xml_tag = next(iterator)


def extract_anchor_links(page):
    # TODO: Read https://en.wikipedia.org/wiki/Help:Wiki_markup
    # TODO: To support all the cases for the links [[Namespace:Page link(, (hidden))|displaylink]]
    # TODO: Support this kind of links display:
    #       San Francisco also has [[public transport]]ation. Examples include [[bus]]es, [[taxicab]]s, and [[tram]]s.
    # TODO: Support this case:
    #       [[#Links and URLs]] is a link to another section on the current page.
    #       [[#Links and URLs|Links and URLs]] is a link to the same section without showing the # symbol.
    # TODO: Check the Namespace is Wikipedia or Nothing
    # TODO: Detect redirect and assing to the same entity
    filter_namespaces = ['File', 'wikt', 'Help', 'Category']  # TODO:: finish the list of namespaces to filter
    link_regex = re.compile("\[\[([^\[\]]*?)\|?\s*([^\|\[\]]*?)\s*\]\]")
    # redirect_regex = re.compile("#REDIRECT\s+\[\[.*?\]\]")
    links = []
    lexicon = []
    for sentence in page.split('\n'):
        # TODO: get rid of the links for the sentence
        for link in link_regex.findall(sentence):
            if not link:
                continue
            # is is not a link to a wiki entity ignore it and continue
            elif link[0].split(':')[0] in filter_namespaces:
                continue
            entity, mention = link
            # if it is too short just continue
            # TODO: this may be too strict
            if len(entity) < 3 or len(mention) < 3:
                continue
            # Sometimes the links are the mentions, in that case make them equal
            if not entity:
                entity = mention
            if not mention:
                mention = entity
            url = format_as_uri(entity)
            if mention and url:
                lexicon.append((url, mention, sentence))
                links.append(url)
    return lexicon, links


def clean_title(title):
    return re.sub(re.compile("|.*"), "", title)


def get_category(page):
    categories = re.findall(re.compile("\[\[Category:(.*?)\]\]"), page)
    categories = [re.sub(re.compile("^(.*?)\|.*$"), r"\1", c).strip() for c in categories]
    categories = [c for c in categories if len(c) > 0]
    return categories


def get_links(xmlf):
    # with click.progressbar(extract_page(xmlf)) as pages:
    lexicon_db = Lexicon()
    for current_title, type, page in extract_page(xmlf):
        current_title = clean_title(current_title)
        current_uri = format_as_uri(current_title)
        categories = get_category(page)
        lexicon = []
        links = []
        if type == 'redirect':
            target_uri = format_as_uri(page)
            # save the redirect as a mention to the uris
            lexicon = [(current_title, target_uri, '')]
            lexicon_db.insert_mentions_uris(lexicon)
            # save the redirect links as links between uris
            lexicon_db.insert_links_uri(current_uri, [target_uri])
        elif page:
            if current_title and len(current_title) > 0 and categories and len(categories) > 0:
                lexicon, links = extract_anchor_links(page)
                # save the mention-uri pairs obtained in the current page
                lexicon_db.insert_mentions_uris(lexicon)
                # save the uris obtained in the page as the links to the current page's uri
                lexicon_db.insert_links_uri(current_uri, links)
                # save the categories obtained for the current page
                lexicon_db.insert_categories_uri(current_uri, categories)
        yield(current_title, categories, lexicon, links)


def format_as_uri(entity):
    return 'https://en.wikipedia.org/wiki/{}'.format('_'.join(entity.split()))


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--file',
                             dest='wiki_file_path',
                             default='./data/wiki.xml',
                             help='Sets the path to wikipedia dump xml file',
                             type=str)
    options = args_parser.parse_args()
    # segment the text in the input files
    count = 0
    for title, categories, entities, links in get_links(options.wiki_file_path):
        count += 1
        if count % 1000 == 0:
            print("currently processing: ")
            print(title, categories, entities, links)
            print('already processed {} pages'.format(count))


if __name__ == '__main__':
    main()
