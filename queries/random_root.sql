-- 500 random mobile root pages (seeded) from the 2026-10-01 crawl.
SELECT page, rank
FROM `httparchive.crawl.pages`
WHERE date = '2026-10-01' AND client = 'mobile' AND is_root_page
ORDER BY FARM_FINGERPRINT(CONCAT(page, 'hd4792'))
LIMIT 500
