CREATE TABLE IF NOT EXISTS `mention_uris` (
    `id` INTEGER PRIMARY KEY,
    `mention` varchar(100) NOT NULL,
    `target_uri` varchar(100) NOT NULL, -- uri the mention is linking to
    `source_uri` varchar(100) NOT NULL, -- uri page where the mention was found
    `sentence` varchar(500) NOT NULL
)
;
