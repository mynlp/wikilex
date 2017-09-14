# wikilex
Wikipedia Entities Lexicon Extractor


Scans a Wikipedia Dump in xml and for each article it extracts the article Title (and generate the proper uri), Categories, Entities (all the mentions, uris, sentence triples), Links (all the entities mentioned in the article)


All this information is saved into a SQLite database using the following structure:

```
Categories {
    id,
    uri,
    category
}

Entities {
    id,
    source_uri,
    link_uri,
    sentence
}

Mentions {
    id,
    mention,
    target_uri, -- uri the mention is linking to
    source_uri, -- uri page where the mention was found
    sentence
}
```

This allows to query easily different potential features for an Entity Linking system.

