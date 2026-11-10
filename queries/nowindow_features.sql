-- Root pages per client hitting the Blink counters for creating HTML documents without a window.
SELECT client, f.feature, COUNT(DISTINCT page) AS pages
FROM `httparchive.crawl.pages`, UNNEST(features) AS f
WHERE date = '2026-10-01' AND is_root_page
  AND f.type = 'default' AND f.id IN ('4462', '2391', '4687')
GROUP BY client, f.feature
ORDER BY client, f.feature
