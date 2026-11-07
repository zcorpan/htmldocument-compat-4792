# Risky code patterns in the 10k-sample bodies (used by cluster_urls.py and make_samples.py).
PATTERNS = {
    'tag_eq_no_fallback': r'"\[object HTMLDocument\]"\s*===?\s*\w|\w\s*===?\s*"\[object HTMLDocument\]"',
    'isHtmlDocument_toString': r'"\[object HTMLDocument\]"===\w+\[\w+\(\d+\)\]\(\)',
    'type_map': r'"\[object HTMLDocument\]":"document"',
    'isType_HTMLDocument': r'\(0,\w+\.\w+\)\(\w+,"HTMLDocument"\)',
    'ctor_name_eq': r'"HTMLDocument"\s*===?\s*\w+\.constructor\.name|constructor\.name\s*===?\s*"HTMLDocument"',
    'indexOf_HTMLDocument': r'indexOf\("HTMLDocument"\)',
    'list_name_members': r'\{\w+:"HTMLDocument",\w+:\["cookie"\]',
    'doc_and_htmldoc_cookie': r'Document:\["cookie"\],\s*HTMLDocument:\["cookie"\]',
    'proto_list': r'window\.HTMLDocument\)\|\|void 0===\w+\?void 0:\w+\.prototype\]',
    'define_both': r'defineProperty\(window\.HTMLDocument\.prototype',
    'instanceof_XMLDocument': r'instanceof\s+XMLDocument',
    'wpmeteor': r'"HTMLDocument::"',
    'currentTarget_tag': r'"\[object HTMLDocument\]"===\w+\.currentTarget',
    'ownerDocument_tag': r'"\[object HTMLDocument\]"===Object\.prototype\.toString\.call\(\w+\.ownerDocument\)',
    'XMLDocument_tag': r'\[object XMLDocument\]',
}
