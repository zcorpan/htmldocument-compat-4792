-- Pages (root and non-root) where Blink counted kXMLDocument (id 77): an XML-parsed document
-- (application/xhtml+xml, XML, SVG) was rendered in some frame of the page.
SELECT client, is_root_page, page, rank
FROM `httparchive.crawl.pages`
WHERE date = '2026-10-01'
  AND EXISTS(SELECT 1 FROM UNNEST(features) WHERE id = '77' AND type = 'default')
