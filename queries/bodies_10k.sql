-- 10k sample: response bodies mentioning HTMLDocument, XMLDocument or a "[object ...Document]" tag.
-- Written to a scratch table (body kept for classification).
SELECT client, is_root_page, page, rank, url, type, FARM_FINGERPRINT(response_body) AS body_fp,
  REGEXP_EXTRACT_ALL(response_body, r'.{0,150}(?:\b(?:HTML|XML)Document\b|\[object (?:HTML|XML)?Document\]).{0,150}') AS snippets,
  response_body AS body
FROM `httparchive.sample_data.requests_10k`
WHERE REGEXP_CONTAINS(response_body, r'\b(?:HTML|XML)Document\b|\[object (?:HTML|XML)?Document\]')
