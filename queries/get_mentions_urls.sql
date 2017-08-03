-- target_words is a variable that would be filled from the calling script
SELECT
    mention
    , uri
FROM
    mention_uris
WHERE
    mention in ({target_words})
;
