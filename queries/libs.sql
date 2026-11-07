-- Pages loading scripts whose behavior changes under a candidate: insuit (accessibility widget;
-- breaks under candidate 2), avplayer (video player; document schema check fails under candidate 2),
-- AudioEye (accessibility; takes its XML-document path only while XHTML documents are XMLDocument).
SELECT client, is_root_page, page, rank,
  CASE WHEN REGEXP_CONTAINS(url, r'insuit\.net/i4tservice/') THEN 'insuit'
       WHEN REGEXP_CONTAINS(url, r'player\.avplayer\.com/script/') THEN 'avplayer'
       WHEN REGEXP_CONTAINS(url, r'audioeye\.com/') THEN 'audioeye' END AS lib
FROM `httparchive.crawl.requests`
WHERE date = '2026-10-01' AND type = 'script'
  AND REGEXP_CONTAINS(url, r'insuit\.net/i4tservice/|player\.avplayer\.com/script/|audioeye\.com/')
GROUP BY 1, 2, 3, 4, 5
