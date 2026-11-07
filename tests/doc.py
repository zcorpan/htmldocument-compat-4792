def main(request, response):
    t = request.GET.first(b"type").decode()
    if t == "image/svg+xml":
        body = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'
    elif t == "text/html":
        body = '<!doctype html><title>x</title>'
    else:
        body = '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>x</title></head><body></body></html>'
    return [(b"Content-Type", t.encode())], body
