# Print a window of the body of one Common Crawl record around a regex match.
# Usage: python3 cc_extract.py WARC URL REGEX [BEFORE] [AFTER]
import re, sys
from cc import html_responses

warc, url, rx = sys.argv[1], sys.argv[2], re.compile(sys.argv[3])
before = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
after = int(sys.argv[5]) if len(sys.argv) > 5 else 1500
for u, text in html_responses(warc):
    if u == url:
        m = rx.search(text)
        print(text[max(0, m.start() - before):m.end() + after] if m else 'NO MATCH')
        break
