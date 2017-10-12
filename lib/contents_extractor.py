from lib.content_cleaner import remove_markup, format_as_uri, is_ignored_namespace
from lib.regular_expressions import RE_LINK_MENTION
import re


def get_mention_uri_context_tuples(source_uri, sentence):
    def is_invalid_link(p, s):
        return p == '<nowiki>' or p.startswith('<ref name=') or \
               s in ['</nowiki>', '<nowiki />'] or s.endswith('</ref>')
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
    tuples = []
    links = []
    for link in link_regex.findall(sentence):
        if not link:
            continue
        # is is not a link to a wiki entity ignore it and continue
        prefix, entity, mention, suffix = link
        if is_ignored_namespace(entity) or is_ignored_namespace(mention) or is_invalid_link(prefix, suffix):
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
            displayed_mention = RE_LINK_MENTION.findall(mention)
            if displayed_mention:
                mention = displayed_mention[0]
        # delete the # from the mention display and delete the "" from the mention (italicizes the displayed word)
        mention = mention.replace('#', '').replace('"', '')
        mention = remove_markup(mention)
        mention = mention.rstrip('\'"-,.:;!?})')
        mention = mention.lstrip('\'"-,.:;!?({')
        mention = mention.replace('\n', '').replace('\r', '')
        url = format_as_uri(entity)
        clean_sentence = remove_markup(sentence)
        tuples.append((mention, url, source_uri, clean_sentence))
        links.append(url)
    return tuples, links


def extract_anchor_links(source_uri, page):
    links = []
    lexicon = []
    for line in page.split('\n'):
        for sentence in line.split('. '):
            new_tuples, new_links = get_mention_uri_context_tuples(source_uri, sentence)
            if new_tuples:
                lexicon.extend(new_tuples)
            if new_links:
                links.extend(new_links)
    return lexicon, list(set(links))  # ignore the repeated links


def get_category(page):
    categories = []
    if page:
        categories = re.findall(re.compile("\[\[Category:(.*?)\]\]"), page)
    if categories:
        categories = [re.sub(re.compile("^(.*?)\|.*$"), r"\1", c).strip() for c in categories]
    categories = [c for c in categories if len(c) > 0]
    return categories
