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
                      'MediaWiki', 'User', 'Help', 'Book', 'Draft', 'wikt',
                      'WikiProject', 'Special', 'Talk', 'Wiktionary', 'media',
                      'User_talk']
MAX_ITERS = 5


def remove_markup(text):
    text = re.sub(RE_P2, "", text)  # remove the last list (=languages)
    # the wiki markup is recursive (markup inside markup etc)
    # instead of writing a recursive grammar, here we deal with that by removing
    # markup in a loop, starting with inner-most expressions and working outwards,
    # for as long as something changes.
    text = remove_template(text)
    text = remove_file(text)
    iterations = 0
    while True:
        old, iterations = text, iterations + 1
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
        # stop if nothing changed between two iterations or after a fixed number of iterations
        if old == text or iterations > MAX_ITERS:
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


def is_tag(current_xml_tag, tag_string):
    return current_xml_tag[1].tag.endswith(tag_string)


def extract_page(xml_file):
    iterator = iterparse(xml_file)
    current_tag = next(iterator)
    title = None
    skip = False
    while current_tag:
        if current_tag[0] == 'end':
            if is_tag(current_tag, "title"):
                title = current_tag[1].text
                skip = False
            if not skip:
                if is_tag(current_tag, "redirect"):
                    redirect = current_tag[1].attrib['title']
                    if redirect:
                        mention = clean_title(title)
                        yield (mention, 'redirect', redirect)
                        skip = True
                        title = None
                elif is_tag(current_tag, "ns"):
                    # if this is page is a template
                    if current_tag[1].text == '10':
                        print(title, "TEMPLATE")
                elif is_tag(current_tag, "text"):
                    link_regex = re.compile(r"#REDIRECT \[\[([^|\[\]]*?)\s*\]\]")
                    text = current_tag[1].text
                    if text:
                        for line in text.split('\n'):
                            redirect_link = link_regex.findall(line)
                            if redirect_link:
                                mention = clean_title(title)
                                yield (mention, 'redirect', redirect_link[0])
                                skip = True
                                title = None
                        yield (title, 'text', text)
                        title = None
        current_tag = next(iterator)


def is_invalid_link(prefix, suffix):
    return prefix == '<nowiki>' or prefix.startswith('<ref name=') or \
           suffix in ['</nowiki>', '<nowiki />'] or suffix.endswith('</ref>')


def get_mention_uri_context_triples(sentence):
    # Details at https://en.wikipedia.org/wiki/Help:Wiki_markup
    # TODO: Support this case:
    #       [[#Links and URLs]] is a link to another section on the current page.
    #       [[#Links and URLs|Links and URLs]] is a link to the same section without showing the # symbol.
    # The regex below return the following groups:
    #       match 1 = '<nowiki>' or <ref_name=...> or ''
    #       match 2 = link or ''
    #       match 3 = mention or ''
    #       match 4 = '</nowiki>' or '<nowiki />' or </ref> or mention's suffix
    prefix_regex = r"(<nowiki>|<ref name=.*?>|)"
    suffix_regex = r"(</nowiki>|,.*?</ref>|<nowiki />|[^<.,\s]*|)"
    wikilink_regex = r"\[\[([^\[\]]*?)\|?\s*([^|\[\]]*?)\s*\]\]"
    link_regex = re.compile(r"{prefix}{link}{suffix}".format(prefix=prefix_regex,
                                                             link=wikilink_regex,
                                                             suffix=suffix_regex))
    triples = []
    links = []
    for link in link_regex.findall(sentence):
        if not link:
            continue
        # is is not a link to a wiki entity ignore it and continue
        prefix, entity, mention, suffix = link
        if entity and entity.split(':')[0] in IGNORED_NAMESPACES:
            continue
        elif mention and mention.split(':')[0] in IGNORED_NAMESPACES:
            continue
        # ignore the links that should be ignored
        if is_invalid_link(prefix, suffix):
            continue
        elif suffix:
            # Support cases like: [[public transport]]ation. or [[bus]]es, [[taxicab]]s, and [[tram]]s.
            mention = mention + suffix
        # if it is too short just continue # TODO: this may be too strict
        if len(entity) < 2 or len(mention) < 2:
            continue
        # Sometimes the links are the mentions, in that case make them equal
        if not entity:
            entity = mention
            # hide the parenthesis from the mention in this case
            link_mention_regex = re.compile(r"^([^\s.:#,]*?) \([^<.,\s]*\)$")
            displayed_mention = link_mention_regex.findall(mention)
            if displayed_mention:
                mention = displayed_mention[0]
        # delete the # from the mention display and delete the "" from the mention (italicizes the displayed word)
        mention = mention.replace('#', '').replace('"', '')
        mention = remove_markup(mention)
        mention = mention.rstrip('\'"-,.:;!?})')
        mention = mention.lstrip('\'"-,.:;!?({')
        url = format_as_uri(entity)
        clean_sentence = remove_markup(sentence)
        triples.append((mention, url, clean_sentence))
        links.append(url)
    return triples, links


def extract_anchor_links(page):
    links = []
    lexicon = []
    for line in page.split('\n'):
        for sentence in line.split('. '):
            new_triples, new_links = get_mention_uri_context_triples(sentence)
            if new_triples:
                lexicon.extend(new_triples)
            if new_links:
                links.extend(new_links)
    return lexicon, list(set(links))  # ignore the repeated links


def clean_title(title):
    if title:
        return re.sub(re.compile("|.*"), "", title)
    else:
        print(title)
        return ''


def get_category(page):
    categories = []
    if page:
        categories = re.findall(re.compile("\[\[Category:(.*?)\]\]"), page)
    else:
        print("get_category: NO PAGE!")
    if categories:
        categories = [re.sub(re.compile("^(.*?)\|.*$"), r"\1", c).strip() for c in categories]
    categories = [c for c in categories if len(c) > 0]
    return categories


def get_links(xmlf, article_numbers):
    lexicon_db = Lexicon()
    article_count = 0
    for current_title, page_type, page in extract_page(xmlf):
        if article_count <= article_numbers:
            continue
        try:
            if not current_title:
                continue
            current_title = clean_title(current_title)
            current_uri = format_as_uri(current_title)
            lexicon = []
            links = []
            categories = []
            try:
                categories = get_category(page)
                if categories:
                    # save the categories obtained for the current page
                    lexicon_db.insert_categories_uri(current_uri, categories)
            except Exception as error:
                print(error)
            if page_type == 'redirect':
                target_uri = format_as_uri(page)
                # save the redirect as a mention to the uris
                lexicon = [(current_title, target_uri, '')]
                lexicon_db.insert_mentions_uris(lexicon)
                # save the redirect links as links between uris
                lexicon_db.insert_links_uri(current_uri, [target_uri])
            elif page:
                lexicon, links = extract_anchor_links(page)
                # save the mention-uri pairs obtained in the current page
                lexicon_db.insert_mentions_uris(lexicon)
                # save the uris obtained in the page as the links to the current page's uri
                lexicon_db.insert_links_uri(current_uri, links)
            yield(current_title, page_type, categories, lexicon, links)
        except Exception as error:
            print(error)
            print("Last article count: ", article_count)
        article_count += 1


def format_as_uri(entity):
    assert entity
    return 'https://en.wikipedia.org/wiki/{}'.format('_'.join(entity.split()))


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--file',
                             dest='wiki_file_path',
                             default='./data/wiki.xml',
                             help='Sets the path to wikipedia dump xml file',
                             type=str)
    args_parser.add_argument('--article_number',
                             dest='article_number',
                             default=-1,
                             help='amount of articles already processed before',
                             type=int)
    options = args_parser.parse_args()
    # segment the text in the input files
    count = 0
    print("Starting the Entity Extraction process...")
    for title, page_type, categories, entities, links in get_links(options.wiki_file_path, options.article_number):
        count += 1
        if count % 1000 == 0:
            print("currently processing: ")
            print("="*65)
            print("Title: ", title)
            print("-" * 65)
            print("Page type: ", page_type)
            print("-" * 65)
            print("Categories: ", categories)
            print("-" * 65)
            print("Entities: ", entities)
            print("-" * 65)
            print("Links: ", links)
            print("=" * 65)
            print('already processed {} pages'.format(count))


if __name__ == '__main__':
    main()
