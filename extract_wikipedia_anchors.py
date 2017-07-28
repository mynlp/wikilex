# TODO: good example: http://www.heatonresearch.com/2017/03/03/python-basic-wikipedia-parsing.html
from lxml.etree import iterparse
from lexicon import Lexicon
import re
# import click
import argparse


def extract_page(xml_file):
    iterator = iterparse(xml_file)
    current_xml_tag = next(iterator)
    title = ''
    redirect_lexicon = {}
    while current_xml_tag:
        if current_xml_tag[0] == 'end':
            if current_xml_tag[1].tag.endswith("title"):
                title = current_xml_tag[1].text
            elif current_xml_tag[1].tag.endswith("redirect"):
                redirect = current_xml_tag[1].attrib['title'].decode("utf-8", "ignore")
                if redirect:
                    mention = clean_title(title)
                    url = 'https://en.wikipedia.org/wiki/{}'.format('_'.join(redirect.decode("utf-8", "ignore").split()))
                    if title not in redirect_lexicon.keys():
                        redirect_lexicon.update({mention: []})
                    redirect_lexicon[mention].append(url)
            elif current_xml_tag[1].tag.endswith("text"):
                yield (title, current_xml_tag[1].text)
                title = ''
        current_xml_tag = next(iterator)
    lexicon = Lexicon()
    lexicon.insert_mentions_urls(redirect_lexicon)


def extract_anchor_links(page):
    # TODO: Read https://en.wikipedia.org/wiki/Help:Wiki_markup
    # To support all the cases for the links [[Namespace:Page link(, (hidden))|displaylink]]
    # Support this kind of links display:
    #       San Francisco also has [[public transport]]ation. Examples include [[bus]]es, [[taxicab]]s, and [[tram]]s.
    # Support this case:
    #       [[#Links and URLs]] is a link to another section on the current page.
    #       [[#Links and URLs|Links and URLs]] is a link to the same section without showing the # symbol.
    # Check the Namespace is Wikipedia or Nothing
    # Detect redirect and assing to the same entity
    filter_namespaces = ['File', 'wikt', 'Help', 'Category'] # TODO:: finish the list of namespaces to filter
    link_regex = re.compile("\[\[([^\[\]]*?)\|?\s*([^\|\[\]]*?)\s*\]\]")
    # redirect_regex = re.compile("#REDIRECT\s+\[\[.*?\]\]")
    links = []
    for sentence in page.split('\n'):
        for link in link_regex.findall(sentence):
            if not link:
                continue
            elif link[0].split(':')[0] in filter_namespaces:
                continue
            entity, mention = link
            if len(entity) < 3 or len(mention) < 3:
                continue
            if not entity:
                entity = mention
            if not mention:
                mention = entity
            url = 'https://en.wikipedia.org/wiki/{}'.format('_'.join(entity.split()))
            if mention and url:
                links.append((url, mention))
    lexicon_update = {}
    # TODO: consider saving into a local db in order to get the count of both
    for url, mention in set(links):
        if mention not in lexicon_update.keys():
            lexicon_update.update({mention: []})
            lexicon_update[mention].append(url)
    lexicon = Lexicon()
    lexicon.insert_mentions_urls(lexicon_update)
    return lexicon_update


def clean_title(title):
    return re.sub(re.compile("|.*"), "", title)


def extract_cat(page):
    cat = re.findall(re.compile("\[\[Category:(.*?)\]\]"), page)
    cat = [re.sub(re.compile("^(.*?)\|.*$"), r"\1", c).strip() for c in cat]
    cat = [c for c in cat if len(c) > 0]
    return cat


def get_links(xmlf):
    # with click.progressbar(extract_page(xmlf)) as pages:
    for title, page in extract_page(xmlf):
        if page:
            title = clean_title(title)
            cat = extract_cat(page)
            if title and len(title) > 0 and cat and len(cat) > 0:
                lexicon = extract_anchor_links(page)
                yield (cat, title, lexicon)


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--file',
                             dest='wiki_file_path',
                             default='./data/wiki.xml',
                             help='Sets the path to wikipedia dump xml file',
                             type=str)
    options = args_parser.parse_args()
    # segment the text in the input files
    for category, _title, entities in get_links(options.wiki_file_path):
        print(category, _title, entities)


if __name__ == '__main__':
    main()
