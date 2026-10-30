from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML_FILE = ROOT / "index.html"
CSS_FILE = ROOT / "css" / "style.css"


class SiteParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.local_refs = []
        self.fragment_refs = []
        self.images_without_alt = []
        self.h1_count = 0
        self.open_tags = []
        self.footer_inside_main = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1_count += 1
        if tag == "img" and not attrs.get("alt", "").strip():
            self.images_without_alt.append(attrs.get("src", "(unknown image)"))
        if tag == "footer" and "main" in self.open_tags:
            self.footer_inside_main = True

        for name in ("src", "href"):
            value = attrs.get(name, "")
            if not value:
                continue
            parts = urlsplit(value)
            if name == "href" and value.startswith("#"):
                self.fragment_refs.append(parts.fragment)
            if parts.scheme or parts.netloc or value.startswith("#"):
                continue
            if parts.path:
                self.local_refs.append(parts.path)

        if tag not in self.VOID:
            self.open_tags.append(tag)

    def handle_endtag(self, tag):
        if tag in self.open_tags:
            index = len(self.open_tags) - 1 - self.open_tags[::-1].index(tag)
            del self.open_tags[index:]


def css_balanced(text):
    depth = 0
    in_comment = False
    quote = None
    escaped = False
    minimum = 0

    index = 0
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""

        if in_comment:
            if char == "*" and nxt == "/":
                in_comment = False
                index += 2
                continue
            index += 1
            continue

        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue

        if char == "/" and nxt == "*":
            in_comment = True
            index += 2
            continue
        if char in ("'", '"'):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            minimum = min(minimum, depth)
        index += 1

    return depth == 0 and minimum == 0 and not in_comment and quote is None


class WebsiteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_FILE.read_text(encoding="utf-8")
        cls.css = CSS_FILE.read_text(encoding="utf-8")
        cls.parser = SiteParser()
        cls.parser.feed(cls.html)
        cls.parser.close()

    def test_all_local_html_assets_exist(self):
        for ref in self.parser.local_refs:
            path = (ROOT / ref.lstrip("/")).resolve()
            with self.subTest(reference=ref):
                self.assertTrue(path.is_file(), f"Missing local file: {ref}")

    def test_all_local_css_assets_exist(self):
        pattern = re.compile(r'''url\(\s*['"]?([^'")]+)''')
        for ref in pattern.findall(self.css):
            if urlsplit(ref).scheme or ref.startswith("data:"):
                continue
            path = (CSS_FILE.parent / urlsplit(ref).path).resolve()
            with self.subTest(reference=ref):
                self.assertTrue(path.is_file(), f"Missing CSS asset: {ref}")

    def test_no_duplicate_html_ids(self):
        seen = set()
        duplicates = set()
        for value in self.parser.ids:
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        self.assertFalse(duplicates, f"Duplicate IDs: {sorted(duplicates)}")

    def test_all_internal_anchors_resolve(self):
        known = set(self.parser.ids)
        broken = sorted(set(self.parser.fragment_refs) - known)
        self.assertFalse(broken, f"Broken in-page links: {broken}")

    def test_images_have_alt_text(self):
        self.assertFalse(
            self.parser.images_without_alt,
            f"Images missing alt text: {self.parser.images_without_alt}",
        )

    def test_page_has_one_h1_and_viewport_metadata(self):
        self.assertEqual(self.parser.h1_count, 1, "Page should have exactly one h1")
        self.assertRegex(
            self.html,
            r"""<meta\s+name=["']viewport["']\s+content=["']width=device-width""",
        )

    def test_footer_is_outside_main_landmark(self):
        self.assertFalse(self.parser.footer_inside_main)

    def test_css_braces_comments_and_strings_are_balanced(self):
        self.assertTrue(css_balanced(self.css), "CSS has unbalanced braces/comment/string")

    def test_hero_index_remains_anchored_to_hero(self):
        self.assertRegex(
            self.css,
            r"""/\* Keep the decorative index anchored to the hero instead of normal flow\. \*/\s*
                \.hero-indicator\s*\{\s*position:\s*absolute""".replace("\n", ""),
        )
        self.assertNotRegex(
            self.css,
            r"""/\.hero-content\s*,\s*\.hero-indicator\s*\{\s*position:\s*relative""",
        )

    def test_phone_technology_grid_uses_one_column(self):
        self.assertRegex(
            self.css,
            r"""/\* Final phone layout for Technology cards\. \*/[\s\S]*?
                @media\s*\(max-width:\s*600px\)\s*\{[\s\S]*?
                \.technology-grid\s*\{\s*grid-template-columns:\s*minmax\(0,\s*1fr\)""".replace("\n", ""),
        )

    def test_about_description_does_not_preserve_source_line_breaks(self):
        self.assertRegex(
            self.css,
            r"""\.about-description\s*\{\s*white-space:\s*normal\s*!important""",
        )
        self.assertIn("<br><br>", self.html)


if __name__ == "__main__":
    unittest.main()
