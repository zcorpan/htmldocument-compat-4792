-- 5,000 random desktop root pages (seeded) from the 2026-10-01 crawl, for the named getter on
-- documents without a window.
SELECT page, rank
FROM `httparchive.crawl.pages`
WHERE date = '2026-10-01' AND client = 'desktop' AND is_root_page
ORDER BY FARM_FINGERPRINT(CONCAT(page, 'hd4792-nowindow'))
LIMIT 5000
