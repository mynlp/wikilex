CREATE TABLE IF NOT EXISTS `mention_entity_stats` (
    `id` INTEGER PRIMARY KEY,
    `mention` varchar(100) NOT NULL,
    `entity` varchar(100) NOT NULL,
    `mention_count` REAL NOT NULL,
    `mention_entity_count` REAL NOT NULL,
    `mention_entity_probability` REAL NOT NULL
)
;

-- Build temp subtable to calculate the counts separatedly
-- Build a similar table for the predicates using DBPedia

-- We refer e' as the most linked entity for anchor s if e' = argmax_e P(ei|s)
--- SELECT entity FROM mention_entity_stats WHERE mention = {mention} ORDER BY mention_entity_probability DESC LIMIT 1;


-- Build a table for the Normalized link Count

-- Build a table for Link probability Pl(s(c)) is the probability that a pharse is used as an anchor in Wikipedia


-- Popularity Features:
-- We have access to 300GBs of Wikipedia page view counts, representing one month worth of page view information
--       we use this as popularity data. (dammit.lt/wikistats) As mentioned in Section3, we find that the most often
--      linked Wikipedia articles might not be the most popular ones on Twitter. Using page view statistics helps our
--      system correct this bias. We define another probability based on page view statistics
--      Pv(ei|c) = v(ei)/(Sum(v(e) from e in E(c)/{NIL}), where v(e) rpresents the view count for the page e.