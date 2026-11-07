# Update status.html: python3 update_status.py STATE LEFT NOW SOFAR (plain text; escaped here).
import html, re, sys
state, left, now, far = sys.argv[1:5]
p = 'status.html'
s = open(p).read()
s = re.sub(r'data-state=\w+ data-left="[^"]*"', f'data-state={state} data-left="{html.escape(left)}"', s)
s = re.sub(r'<p><b>Now:</b> .*', '<p><b>Now:</b> ' + html.escape(now), s)
s = re.sub(r'<p><b>So far:</b> .*', '<p><b>So far:</b> ' + html.escape(far), s)
open(p, 'w').write(s)
