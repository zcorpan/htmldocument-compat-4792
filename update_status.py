# Update status.html (template from the httparchive skill): python3 update_status.py STATE LEFT NOW SOFAR
# STATE: running, waiting or done; LEFT: e.g. "About 1 h left (phase 2/6)" (ignored unless running).
import html, re, sys
state, left, now, far = sys.argv[1:5]
emoji, line = {'running': ('⏳', left or 'Running'), 'waiting': ('✋', 'Waiting on you'), 'done': ('✅', 'Done')}[state]
repo = 'htmldocument-compat-4792'
p = 'status.html'
s = open(p).read()
s = re.sub(r'<title>.*?</title>', f'<title>{html.escape(line)} · {repo}</title>', s)
s = re.sub(r"<text y='.9em' font-size='90'>.*?</text>", f"<text y='.9em' font-size='90'>{emoji}</text>", s)
s = re.sub(r'<h1>.*?</h1>', f'<h1>{repo}</h1>', s)
s = re.sub(r'<p><b>\S+ [^<]*</b>\n', f'<p><b>{emoji} {html.escape(line)}</b>\n', s, count=1)
s = re.sub(r'<p><b>Now:</b> .*', '<p><b>Now:</b> ' + html.escape(now), s)
s = re.sub(r'<p><b>So far:</b> .*', '<p><b>So far:</b> ' + html.escape(far), s)
open(p, 'w').write(s)
