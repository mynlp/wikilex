CREATE TABLE IF NOT EXISTS `mention_uris` (
    `id` INTEGER PRIMARY KEY,
    `mention` varchar(100) NOT NULL,
    `uri` varchar(100) NOT NULL,
    `sentence` varchar(500) NOT NULL
)
;
