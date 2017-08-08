# TODO: good example: http://www.heatonresearch.com/2017/03/03/python-basic-wikipedia-parsing.html
from lxml.etree import iterparse
from lexicon import Lexicon
import argparse
import re

RE_P0 = re.compile('<!--.*?-->', re.DOTALL | re.UNICODE)  # comments
RE_P1 = re.compile('<ref([> ].*?)(</ref>|/>)', re.DOTALL | re.UNICODE)  # footnotes
RE_P2 = re.compile("(\n\[\[[a-z][a-z][\w-]*:[^:\]]+\]\])+$", re.UNICODE)  # links to languages
RE_P3 = re.compile("{{([^}{]*)}}", re.DOTALL | re.UNICODE)  # template
RE_P4 = re.compile("{{([^}]*)}}", re.DOTALL | re.UNICODE)  # template
RE_P5 = re.compile('\[(\w+):\/\/(.*?)(( (.*?))|())\]', re.UNICODE)  # remove URL, keep description
RE_P6 = re.compile("\[([^][]*)\|([^][]*)\]", re.DOTALL | re.UNICODE)  # simplify links, keep description
RE_P7 = re.compile('\n\[\[[iI]mage(.*?)(\|.*?)*\|(.*?)\]\]', re.UNICODE)  # keep description of images
RE_P8 = re.compile('\n\[\[[fF]ile(.*?)(\|.*?)*\|(.*?)\]\]', re.UNICODE)  # keep description of files
RE_P9 = re.compile('<nowiki([> ].*?)(</nowiki>|/>)', re.DOTALL | re.UNICODE)  # outside links
RE_P10 = re.compile('<math([> ].*?)(</math>|/>)', re.DOTALL | re.UNICODE)  # math content
RE_P11 = re.compile('<(.*?)>', re.DOTALL | re.UNICODE)  # all other tags
RE_P12 = re.compile('\n(({\|)|(\|-)|(\|}))(.*?)(?=\n)', re.UNICODE)  # table formatting
RE_P13 = re.compile('\n(\||\!)(.*?\|)*([^|]*?)', re.UNICODE)  # table cell formatting
RE_P14 = re.compile('\[\[Category:[^][]*\]\]', re.UNICODE)  # categories
# Remove File and Image template
RE_P15 = re.compile('\[\[([fF]ile:|[iI]mage)[^]]*(\]\])', re.UNICODE)

# MediaWiki namespaces (https://www.mediawiki.org/wiki/Manual:Namespace) that
# ought to be ignored
IGNORED_NAMESPACES = ['Wikipedia', 'Category', 'File', 'Portal', 'Template',
                      'MediaWiki', 'User', 'Help', 'Book', 'Draft',
                      'WikiProject', 'Special', 'Talk']

MAX_ITERS = 5

def remove_markup(text):
    text = re.sub(RE_P2, "", text)  # remove the last list (=languages)
    # the wiki markup is recursive (markup inside markup etc)
    # instead of writing a recursive grammar, here we deal with that by removing
    # markup in a loop, starting with inner-most expressions and working outwards,
    # for as long as something changes.
    text = remove_template(text)
    text = remove_file(text)
    iters = 0
    while True:
        old, iters = text, iters + 1
        text = re.sub(RE_P0, "", text)  # remove comments
        text = re.sub(RE_P1, '', text)  # remove footnotes
        text = re.sub(RE_P9, "", text)  # remove outside links
        text = re.sub(RE_P10, "", text)  # remove math content
        text = re.sub(RE_P11, "", text)  # remove all remaining tags
        text = re.sub(RE_P14, '', text)  # remove categories
        text = re.sub(RE_P5, '\\3', text)  # remove urls, keep description
        text = re.sub(RE_P6, '\\2', text)  # simplify links, keep description only
        # remove table markup
        text = text.replace('||', '\n|')  # each table cell on a separate line
        text = re.sub(RE_P12, '\n', text)  # remove formatting lines
        text = re.sub(RE_P13, '\n\\3', text)  # leave only cell content
        # remove empty mark-up
        text = text.replace('[]', '')
        if old == text or iters > MAX_ITERS:  # stop if nothing changed between two iterations or after a fixed number of iterations
            break

    # the following is needed to make the tokenizer see '[[socialist]]s' as a single word 'socialists'
    # TODO is this really desirable?
    text = text.replace('[', '').replace(']', '')  # promote all remaining markup to plain text
    return text


def remove_template(s):
    """Remove template wikimedia markup.
    Return a copy of `s` with all the wikimedia markup template removed. See
    http://meta.wikimedia.org/wiki/Help:Template for wikimedia templates
    details.
    Note: Since template can be nested, it is difficult remove them using
    regular expresssions.
    """
    # Find the start and end position of each template by finding the opening
    # '{{' and closing '}}'
    n_open, n_close = 0, 0
    starts, ends = [], []
    in_template = False
    prev_c = None
    for i, c in enumerate(iter(s)):
        if not in_template:
            if c == '{' and c == prev_c:
                starts.append(i - 1)
                in_template = True
                n_open = 1
        if in_template:
            if c == '{':
                n_open += 1
            elif c == '}':
                n_close += 1
            if n_open == n_close:
                ends.append(i)
                in_template = False
                n_open, n_close = 0, 0
        prev_c = c

    # Remove all the templates
    s = ''.join([s[end + 1:start] for start, end in
                 zip(starts + [None], [-1] + ends)])

    return s


def remove_file(s):
    """Remove the 'File:' and 'Image:' markup, keeping the file caption.
    Return a copy of `s` with all the 'File:' and 'Image:' markup replaced by
    their corresponding captions. See http://www.mediawiki.org/wiki/Help:Images
    for the markup details.
    """
    # The regex RE_P15 match a File: or Image: markup
    for match in re.finditer(RE_P15, s):
        m = match.group(0)
        caption = m[:-2].split('|')[-1]
        s = s.replace(m, caption, 1)
    return s


def extract_page(xml_file):
    iterator = iterparse(xml_file)
    current_xml_tag = next(iterator)
    title = None
    while current_xml_tag:
        if current_xml_tag[0] == 'end':
            if current_xml_tag[1].tag.endswith("title"):
                title = current_xml_tag[1].text
            elif current_xml_tag[1].tag.endswith("redirect"):
                redirect = current_xml_tag[1].attrib['title']
                if redirect:
                    mention = clean_title(title)
                    yield (mention, 'redirect', redirect)
            elif current_xml_tag[1].tag.endswith("ns"):
                # if this is page is a template
                if current_xml_tag[1].text == '10':
                    print(title, "TEMPLATE")
            elif current_xml_tag[1].tag.endswith("text"):
                yield (title, 'text', current_xml_tag[1].text)
                title = None
        current_xml_tag = next(iterator)


def extract_anchor_links(page):
    # TODO: Read https://en.wikipedia.org/wiki/Help:Wiki_markup
    # TODO: Support this kind of links display:
    #       San Francisco also has [[public transport]]ation. Examples include [[bus]]es, [[taxicab]]s, and [[tram]]s.
    # TODO: Support this case:
    #       [[#Links and URLs]] is a link to another section on the current page.
    #       [[#Links and URLs|Links and URLs]] is a link to the same section without showing the # symbol.
    link_regex = re.compile("\[\[([^\[\]]*?)\|?\s*([^\|\[\]]*?)\s*\]\]")
    links = []
    lexicon = []
    for sentence in page.split('\n'):
        for link in link_regex.findall(sentence):
            if not link:
                continue
            # is is not a link to a wiki entity ignore it and continue
            elif link[0].split(':')[0] in IGNORED_NAMESPACES \
                    or link[1].split(':')[0] in IGNORED_NAMESPACES:
                continue
            entity, mention = link
            # if it is too short just continue
            # TODO: this may be too strict
            if len(entity) < 2 or len(mention) < 2:
                continue
            # Sometimes the links are the mentions, in that case make them equal
            if not entity:
                entity = mention
            if not mention:
                mention = entity
            url = format_as_uri(entity)
            if mention and url:
                clean_text = remove_markup(sentence)
                sentences = clean_text.split('. ')
                for clean_sentence in sentences:
                    if mention in clean_sentence:
                        lexicon.append((mention, url, clean_sentence))
                links.append(url)
    return lexicon, list(set(links))  # ignore the repeated links


def clean_title(title):
    return re.sub(re.compile("|.*"), "", title)


def get_category(page):
    if page:
        categories = re.findall(re.compile("\[\[Category:(.*?)\]\]"), page)
    else:
        print("get_category: NO PAGE!")
    if categories:
        categories = [re.sub(re.compile("^(.*?)\|.*$"), r"\1", c).strip() for c in categories]
    categories = [c for c in categories if len(c) > 0]
    return categories


def get_links(xmlf):
    # with click.progressbar(extract_page(xmlf)) as pages:
    lexicon_db = Lexicon()
    for current_title, type, page in extract_page(xmlf):
        current_title = clean_title(current_title)
        current_uri = format_as_uri(current_title)
        try:
            categories = get_category(page)
        except Exception as error:
            print(error)
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
        if count % 10000 == 0:
            print("currently processing: ")
            print("Title: ", title)
            print("Categories: ", categories)
            print("Entities: ", entities)
            print("Links: ", links)
            print('already processed {} pages'.format(count))


if __name__ == '__main__':
    main()
