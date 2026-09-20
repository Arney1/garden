"""Security regressions for graph markup and published attachments."""
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote

from build import Garden, build
from transit_reader import Tagged


class Markup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'assets').mkdir()
        self.config = {'home_page': 'Home', 'title': 'Garden', 'navigation': [], 'description': 'Notes'}
        self.nodes = {1: {'block/name': 'home', 'block/title': 'Home',
                          'block/uuid': '11111111-1111-4111-8111-111111111111'}}
        self.g = Garden(self.nodes, self.source, self.config)

    def test_graph_text_cannot_inject_elements_or_script_urls(self):
        for payload in ('<script>alert(1)</script>', '<img src=x onerror=alert(1)>',
                        '[click](javascript:alert%281%29)', '![image](javascript:alert%281%29)',
                        '[click](data:text/html;base64,PHNjcmlwdD4=)',
                        '[click](jav&#x61;script:alert%281%29)',
                        '```html\n<script>alert(1)</script>\n```'):
            with self.subTest(payload=payload):
                for tag, attrs in Markup(self.g.md.render(payload)).elements:
                    self.assertNotIn(tag, ('script', 'iframe', 'object', 'embed'))
                    self.assertFalse(any(k.startswith('on') for k in attrs))
                    for attr in ('href', 'src'):
                        self.assertFalse(attrs.get(attr, '').lower().startswith(('javascript:', 'data:', 'vbscript:')))

    def test_unsafe_schemes_are_rejected(self):
        for url in ('javascript:alert(1)', 'JaVaScRiPt:alert(1)', 'java\nscript:alert(1)',
                    'data:text/html,hello', 'file:///etc/passwd'):
            with self.subTest(url=url):
                self.assertEqual(self.g.link_url(url), '#')

    def test_traversal_and_symlinks_cannot_publish_files_outside_assets(self):
        secret = self.source / 'secret.txt'
        secret.write_text('private fixture')
        (self.source / 'assets/link.txt').symlink_to(secret)
        for url in ('assets/../secret.txt', 'assets/%2e%2e/secret.txt',
                    'assets/..\\secret.txt', 'assets/link.txt'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.g.asset_url(url)
        (self.source / 'assets/link.txt').unlink()
        (self.source / 'assets').rmdir()
        (self.source / 'assets').symlink_to(self.root)
        with self.assertRaises(ValueError):
            self.g.asset_url('assets/example.txt')

    def test_non_media_attachments_are_download_links_with_original_filenames(self):
        for name in ('demo.html', 'image.SVG', 'script.js', 'notes.txt', 'slides.pptx', 'binary', 'quote".html'):
            with self.subTest(name=name):
                (self.source / 'assets' / name).write_text('<script>window.attachmentRan = true</script>')
                url = self.g.asset_url('assets/' + name)
                self.assertEqual(unquote(url), '/downloads/' + name + '.download')
        for syntax in ('[sample](assets/demo.html)', '![sample](assets/demo.html)', '![sample](assets/image.SVG)'):
            elements = Markup(self.g.md.render(syntax)).elements
            self.assertFalse(any(tag == 'img' for tag, _ in elements))
            link = next(attrs for tag, attrs in elements if tag == 'a')
            self.assertTrue(link['href'].startswith('/downloads/'))
            self.assertIn(link['download'], ('demo.html', 'image.SVG'))

    def test_inline_formats_keep_their_urls_and_pdf_fragments(self):
        for name in ('image.png', 'photo.JPG', 'clip.mp4', 'audio.ogg', 'paper.pdf'):
            (self.source / 'assets' / name).write_bytes(b'fixture')
            self.assertEqual(self.g.asset_url('../assets/' + name), '/assets/' + name)
        self.assertEqual(self.g.asset_url('assets/paper.pdf#page=8'), '/assets/paper.pdf#page=8')
        self.assertTrue(any(tag == 'img' for tag, _ in Markup(self.g.md.render('![photo](assets/image.png)')).elements))
        remote = 'https://example.com/downloads/photo.png'
        image = next(attrs for tag, attrs in Markup(self.g.md.render(f'![photo]({remote})')).elements if tag == 'img')
        self.assertEqual(image['src'], remote)

    def test_svg_entity_reference_is_a_download_not_an_inline_image(self):
        uuid = '22222222-2222-4222-8222-222222222222'
        self.nodes[2] = {'block/title': 'Diagram', 'block/uuid': uuid, 'logseq.property.asset/type': 'svg'}
        (self.source / 'assets' / (uuid + '.svg')).write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        elements = Markup(self.g.asset_html(2)).elements
        self.assertFalse(any(tag == 'img' for tag, _ in elements))
        link = next(attrs for tag, attrs in elements if tag == 'a')
        self.assertEqual(link['download'], uuid + '.svg')
        self.g.property_entities['user.property/diagram'] = {'block/title': 'Diagram', 'db/valueType': 'db.type/ref'}
        prop = self.g.properties({'user.property/diagram': 2})
        self.assertIn('download="' + uuid + '.svg"', prop)

    def test_build_copies_active_files_only_to_downloads_and_emits_protective_headers(self):
        payload = '<script>window.attachmentRan = true</script>'
        (self.source / 'assets/demo.html').write_text(payload)
        (self.source / 'assets/photo.png').write_bytes(b'fixture')
        (self.source / 'index.html').write_text('export fixture')
        self.nodes[2] = {'block/title': '[Demo](assets/demo.html) ![Photo](assets/photo.png)',
                         'block/uuid': '22222222-2222-4222-8222-222222222222',
                         'block/page': 1, 'block/parent': 1}
        db = {'schema': {}, 'datoms': [Tagged('datascript/Datom', [eid, attr, value])
                                     for eid, node in self.nodes.items() for attr, value in node.items()]}
        output = self.root / 'dist'
        with patch('build.load_export', return_value=db):
            build(self.source, output, self.config)
        self.assertFalse((output / 'assets/demo.html').exists())
        self.assertEqual((output / 'downloads/demo.html.download').read_text(), payload)
        self.assertEqual((output / 'assets/photo.png').read_bytes(), b'fixture')
        self.assertIn('download="demo.html"', (output / 'index.html').read_text())
        self.assertIn('href="/licenses/"', (output / 'index.html').read_text())
        self.assertTrue((output / 'licenses/index.html').is_file())
        self.assertIn('Permission is hereby granted', (output / 'licenses/MIT.txt').read_text())
        self.assertTrue((output / 'licenses/pygments/LICENSE.txt').is_file())
        self.assertTrue((output / 'licenses/THIRD_PARTY_NOTICES.md').is_file())
        headers = (output / '_headers').read_text()
        self.assertIn("script-src 'self'", headers)
        self.assertIn("frame-ancestors 'none'", headers)
        self.assertIn('X-Frame-Options: DENY', headers)
        self.assertIn('X-Content-Type-Options: nosniff', headers)
        downloads = headers.split('/downloads/*\n')[1].split('\n\n')[0]
        self.assertIn('Content-Type: application/octet-stream', downloads)
        self.assertIn('Content-Disposition: attachment', downloads)
        self.assertIn('Content-Security-Policy: sandbox;', downloads)
        self.assertNotIn("'unsafe-inline'", headers)
        self.assertNotIn("'unsafe-eval'", headers)

    def test_missing_license_does_not_replace_previous_site(self):
        output = self.root / 'dist'
        output.mkdir()
        (output / '.static-garden-build').write_text('fixture')
        (output / 'index.html').write_text('previous site')
        with patch('build.HERE', self.source / 'static-garden'):
            with self.assertRaisesRegex(ValueError, 'Required license notice missing'):
                build(self.source, output, self.config)
        self.assertEqual((output / 'index.html').read_text(), 'previous site')


if __name__ == '__main__':
    unittest.main()
