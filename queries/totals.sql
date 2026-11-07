SELECT client, is_root_page, COUNT(0) AS pages
FROM `httparchive.crawl.pages` WHERE date = '2026-10-01' GROUP BY 1, 2 ORDER BY 1, 2
