-- Main documents served with an XML MIME type (application/xhtml+xml, */xml, */*+xml).
SELECT client, is_root_page, page, rank, url, JSON_VALUE(summary, '$.mimeType') AS mime
FROM `httparchive.crawl.requests`
WHERE date = '2026-10-01' AND is_main_document
  AND REGEXP_CONTAINS(LOWER(JSON_VALUE(summary, '$.mimeType')), r'xml')
