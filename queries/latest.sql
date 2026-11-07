SELECT MAX(date) AS d FROM `httparchive.crawl.pages` WHERE date >= '2026-08-01' AND client = 'mobile' AND is_root_page
