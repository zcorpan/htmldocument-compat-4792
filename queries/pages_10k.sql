SELECT client, is_root_page, COUNT(0) AS pages FROM `httparchive.sample_data.pages_10k` GROUP BY 1, 2 ORDER BY 1, 2
