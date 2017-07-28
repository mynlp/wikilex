-- target_words is a variable that would be filled from the calling script
SELECT
    mention
    , url
FROM
    lexicon
WHERE
    mention in ({target_words})
;
