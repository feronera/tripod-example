"""Small HTML tree for page tests (standard library only, no app imports)."""

from html.parser import HTMLParser

VOID = frozenset("area base br col embed hr img input link meta source track wbr".split())


class Element:
    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = {name: "" if value is None else value for name, value in attrs}
        self.parent = parent
        self.children = []

    def elements(self, templates=False):
        """Descendant elements in document order; template content only when asked."""
        for child in self.children:
            if isinstance(child, Element):
                yield child
                if child.tag != "template" or templates:
                    yield from child.elements(templates)

    def find_all(self, tag=None, attrs=None, templates=False):
        """Elements with this tag and these attributes (a value of None means present)."""
        found = []
        for el in self.elements(templates):
            if tag is not None and el.tag != tag:
                continue
            if attrs and any(
                name not in el.attrs or (value is not None and el.attrs[name] != value)
                for name, value in attrs.items()
            ):
                continue
            found.append(el)
        return found

    def text(self):
        """Visible text with whitespace collapsed; skips script, style and nested templates."""
        return " ".join("".join(self._strings()).split())

    def _strings(self):
        for child in self.children:
            if isinstance(child, str):
                yield child
            elif child.tag not in ("script", "style", "template"):
                yield from child._strings()

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", [], None)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        el = Element(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(el)
        if tag not in VOID:
            self.stack.append(el)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Element(tag, attrs, self.stack[-1]))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse(body):
    """Parse a page body (bytes or str) into an Element tree."""
    builder = _TreeBuilder()
    builder.feed(body.decode("utf-8") if isinstance(body, bytes) else body)
    builder.close()
    return builder.root


def by_text(root, text, templates=False):
    """Innermost elements whose whole text equals `text`."""
    return [
        el for el in root.elements(templates)
        if el.text() == text
        and not any(isinstance(c, Element) and c.text() == text for c in el.children)
    ]
