from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import re
import struct
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


def image_size(path):
    """Return (width, height) for PNG, JPEG or WebP using only the standard library."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                index += 2
                continue
            length = struct.unpack(">H", data[index + 2:index + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                height, width = struct.unpack(">HH", data[index + 5:index + 9])
                return width, height
            index += 2 + length
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        kind = data[12:16]
        if kind == b"VP8X":
            return (1 + int.from_bytes(data[24:27], "little"),
                    1 + int.from_bytes(data[27:30], "little"))
        if kind == b"VP8L":
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if kind == b"VP8 ":
            width, height = struct.unpack("<HH", data[26:30])
            return width & 0x3FFF, height & 0x3FFF
    return None


class LinkNameParser(HTMLParser):
    """Collects each link's accessible text, ignoring aria-hidden descendants."""
    VOID = SiteParser.VOID

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []          # (classes, href, name)
        self._stack = []         # (tag, hidden)
        self._current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = attrs.get("aria-hidden") == "true"
        if tag == "a":
            self._current = {"classes": attrs.get("class", ""), "href": attrs.get("href", ""),
                             "label": attrs.get("aria-label"), "text": [], "depth": len(self._stack)}
        if tag not in self.VOID:
            self._stack.append((tag, hidden))

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        while self._stack and self._stack[-1][0] != tag:
            self._stack.pop()
        if self._stack:
            self._stack.pop()
        if tag == "a" and self._current is not None:
            name = self._current["label"] or " ".join(" ".join(self._current["text"]).split())
            self.links.append((self._current["classes"], self._current["href"], name))
            self._current = None

    def handle_data(self, data):
        if self._current is not None and not any(hidden for _, hidden in self._stack[self._current["depth"]:]):
            self._current["text"].append(data)


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
        blocks = re.findall(r"\.hero-indicator\s*\{([^}]*)\}", self.css)
        self.assertTrue(
            any(re.search(r"position\s*:\s*absolute", block) for block in blocks),
            "The hero index must have absolute positioning",
        )
        self.assertNotRegex(
            self.css,
            r"\.hero-content\s*,\s*\.hero-indicator\s*\{\s*position\s*:\s*relative",
        )

    def test_phone_technology_grid_uses_one_column(self):
        marker = "/* Final phone layout for Technology cards. */"
        self.assertIn(marker, self.css)
        mobile_rules = self.css.split(marker, 1)[1]
        match = re.search(r"\.technology-grid\s*\{([^}]*)\}", mobile_rules)
        self.assertIsNotNone(match, "Mobile technology grid rule is missing")
        self.assertRegex(
            match.group(1),
            r"grid-template-columns:\s*minmax\(0,\s*1fr\)",
        )

    def test_about_description_does_not_preserve_source_line_breaks(self):
        self.assertRegex(
            self.css,
            r"""\.about-description\s*\{\s*white-space:\s*normal\s*!important""",
        )
        self.assertIn("<br><br>", self.html)


    # ---- Regression tests from the stress-test pass ----

    def test_images_are_not_oversized(self):
        """Huge originals (e.g. 8478x5652) cost megabytes and stall scrolling while they decode."""
        limits = {"images": (2600, 600 * 1024), "logos": (512, 150 * 1024)}
        for folder, (max_edge, max_bytes) in limits.items():
            for path in sorted((ROOT / "assets" / folder).iterdir()):
                if path.suffix.lower() == ".svg":
                    continue
                with self.subTest(file=f"{folder}/{path.name}"):
                    self.assertLessEqual(path.stat().st_size, max_bytes,
                                         f"{path.name} is {path.stat().st_size // 1024} KB")
                    size = image_size(path)
                    self.assertIsNotNone(size, f"Could not read dimensions of {path.name}")
                    self.assertLessEqual(max(size), max_edge, f"{path.name} is {size[0]}x{size[1]}")

    def test_video_source_is_chosen_by_script_not_markup(self):
        """A <source> in the markup races the reduced-motion guard and gets fetched anyway."""
        self.assertIsNone(re.search(r"<source[\s/]", self.html), "Remove the <source> element")
        urls = re.findall(r'data-src(?:-small)?="([^"]+)"', self.html)
        self.assertEqual(len(urls), 2, "Expected data-src and data-src-small on the hero video")
        for url in urls:
            with self.subTest(video=url):
                self.assertTrue((ROOT / url).is_file(), f"Missing video file: {url}")
        small = ROOT / re.search(r'data-src-small="([^"]+)"', self.html).group(1)
        self.assertLessEqual(small.stat().st_size, 3 * 1024 * 1024, "Small-screen video should stay under 3 MB")

    def test_reduced_motion_returns_before_video_source_is_assigned(self):
        script = re.search(r"<script>(.*?hero-video.*?)</script>", self.html, re.S)
        self.assertIsNotNone(script, "Hero video script is missing")
        body = script.group(1)
        guard = body.index("prefers-reduced-motion")
        early_return = body.index("return;", guard)
        assignment = body.index("video.src")
        self.assertLess(early_return, assignment,
                        "Reduced-motion visitors must leave the script before video.src is set")

    def test_no_script_visitors_still_get_hero_image(self):
        self.assertRegex(self.html, r"<noscript>\s*<style>[^<]*\.hero[^<]*server-room\.jpg")

    def test_decorative_arrows_are_hidden_from_assistive_technology(self):
        arrows = re.findall(r"<span([^>]*)>\s*([\u2197\u2191])\s*</span>", self.html)
        self.assertGreaterEqual(len(arrows), 9, "Expected the decorative arrow spans to be present")
        for attributes, glyph in arrows:
            with self.subTest(glyph=glyph, attributes=attributes):
                self.assertIn('aria-hidden="true"', attributes)
        self.assertNotRegex(self.html, r"BACK TO TOP\s*[\u2191]")

    def test_service_links_have_distinct_accessible_names(self):
        parser = LinkNameParser()
        parser.feed(self.html)
        names = [name for classes, _href, name in parser.links if "service-link" in classes.split()]
        self.assertEqual(len(names), 3)
        self.assertEqual(len(set(names)), 3, f"Identical link names: {names}")
        for name in names:
            self.assertTrue(name.upper().startswith("DISCUSS YOUR REQUIREMENTS"),
                            "Visible label must stay at the start of the accessible name")

    def test_visually_hidden_utility_exists(self):
        self.assertRegex(self.css, r"\.visually-hidden\s*\{[^}]*clip")

    def test_favicon_is_declared_and_exists(self):
        match = re.search(r'<link\s+rel="icon"[^>]*href="([^"]+)"', self.html)
        self.assertIsNotNone(match, "No <link rel=\"icon\"> found")
        self.assertTrue((ROOT / match.group(1)).is_file())

    def test_smallest_phones_shrink_headlines(self):
        match = re.search(r"@media\s*\(max-width:\s*300px\)\s*\{(.*?)\n\}", self.css, re.S)
        self.assertIsNotNone(match, "Missing the max-width: 300px headline rule")
        self.assertIn(".hero h1", match.group(1))
        self.assertIn(".contact-content h2", match.group(1))


if __name__ == "__main__":
    unittest.main()
