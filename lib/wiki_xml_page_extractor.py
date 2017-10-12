from lxml.etree import iterparse
from lib.content_cleaner import clean_title
from lib.regular_expressions import RE_REDIRECT


def extract_page(xml_file):
    def is_tag(current_xml_tag, tag_string):
        return current_xml_tag[1].tag.endswith(tag_string)

    iterator = iterparse(xml_file)
    current_tag = next(iterator)
    title = None
    valid_content = True
    while current_tag:
        if current_tag[0] == 'end':
            if is_tag(current_tag, "title"):
                title = current_tag[1].text
                valid_content = True
            if valid_content:
                if is_tag(current_tag, "redirect"):
                    redirect = current_tag[1].attrib['title']
                    if redirect:
                        mention = clean_title(title)
                        yield (mention, 'redirect', redirect)
                        valid_content = False
                        title = None
                elif title and ':Template' in title or \
                        (is_tag(current_tag, "ns") and current_tag[1].text == '10'):
                        valid_content = False
                        title = None
                elif is_tag(current_tag, "text"):
                    text = current_tag[1].text
                    if text:
                        if RE_REDIRECT.findall(text):
                            mention = clean_title(title)
                            yield (mention, 'redirect', RE_REDIRECT.findall(text)[0])
                            valid_content = False
                        else:
                            yield (title, 'text', text)
                        title = None
        current_tag = next(iterator)
