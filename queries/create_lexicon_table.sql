CREATE TABLE IF NOT EXISTS `lexicon` (
    `mention_id` INTEGER PRIMARY KEY,
    `mention` varchar(100) NOT NULL,
    `url` varchar(100) NOT NULL
)
;