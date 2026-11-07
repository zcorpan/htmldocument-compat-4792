-- 10k sample: subframe documents (iframes, object/embed) served with an XML MIME type.
SELECT client, is_root_page, page, rank, url, JSON_VALUE(summary, '$.mimeType') AS mime
FROM `httparchive.sample_data.requests_10k`
WHERE NOT is_main_document
  AND REGEXP_CONTAINS(LOWER(JSON_VALUE(summary, '$.mimeType')), r'xml')
  AND JSON_VALUE(payload, '$._request_type') = 'Document'
