-- Seeded samples of desktop root pages (2026-10-01) hitting Blink counters for creating HTML
-- documents without a window: 2,000 with XMLHttpRequestResponseXML (2391), 1,000 with
-- ParseHTMLUnsafe (4687).
WITH hits AS (
  SELECT DISTINCT page, rank, f.feature AS stratum
  FROM `httparchive.crawl.pages`, UNNEST(features) AS f
  WHERE date = '2026-10-01' AND client = 'desktop' AND is_root_page
    AND f.type = 'default' AND f.id IN ('2391', '4687')
)
SELECT stratum, page, rank
FROM hits
QUALIFY ROW_NUMBER() OVER (PARTITION BY stratum ORDER BY FARM_FINGERPRINT(CONCAT(page, 'hd4792-nowindow-strata')))
  <= IF(stratum = 'XMLHttpRequestResponseXML', 2000, 1000)
ORDER BY stratum, FARM_FINGERPRINT(CONCAT(page, 'hd4792-nowindow-strata'))
