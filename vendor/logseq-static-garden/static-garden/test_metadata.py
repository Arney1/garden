"""DB metadata, launcher directory, and publisher-only presentation regressions."""
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from build import Garden, HERE, build
from icons import render_icon
from test_build import node


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name)
        self.config = {'home_page': 'Home', 'title': 'Garden', 'description': 'Notes', 'navigation': []}
        self.nodes = {1: node('Home', 'home', **{'block/name': 'home'})}

    def block(self, eid, style=None, parent=1):
        data = {'block/parent': parent, 'block/page': 1, 'block/order': f'{eid:03}'}
        if style is not None:
            data['logseq.property/order-list-type'] = style
        self.nodes[eid] = node(f'Item {eid}', str(eid), **data)

    def test_numbering_is_per_sibling_level_and_survives_mixed_lists(self):
        self.block(2, 'number')
        self.block(3, 'number')
        self.block(4)
        self.block(5, 'number')
        self.block(6, 'number', parent=2)
        self.block(7, 'number', parent=2)
        g = Garden(self.nodes, self.source, self.config)
        html = g.page_content(1)
        tags = Tags(html).tags
        ordered = [attrs for tag, attrs in tags if tag == 'ol']
        self.assertEqual(len(ordered), 3)
        self.assertEqual(ordered[-1]['start'], '3')
        self.assertIn('aria-label="Link to this block">3.</a>', html)
        self.assertEqual(html.count('aria-label="Link to this block">1.</a>'), 2)
        self.assertEqual(html.count('aria-label="Link to this block">•</a>'), 1)
        self.assertIn('<details open>', html)
        self.assertIn('id="block-7"', html)

    def test_closed_values_and_omitted_public_export_references(self):
        self.nodes[10] = {'logseq.property/value': 'number'}
        self.nodes[11] = {'block/title': 'bullet'}
        for eid, style in [(2, 10), (3, 98765), (4, 11), (5, False), (6, 'bullet')]:
            self.block(eid, style)
        g = Garden(self.nodes, self.source, self.config)
        self.assertEqual([g.numbered(i) for i in range(2, 7)], [True, True, False, False, False])
        self.assertEqual(len(g.warnings), 1)

    def test_numbered_page_and_block_embeds_use_the_same_outline_rule(self):
        self.block(2, 'number')
        g = Garden(self.nodes, self.source, self.config)
        for target in [1, 2]:
            html = g.embed(target, ())
            self.assertIn('<ol class="outline">', html)
            self.assertIn('aria-label="Link to this block">1.</a>', html)

    def test_emoji_ids_skin_variants_and_tabler_filled_icons(self):
        self.assertIn('🎓', render_icon({'type': 'emoji', 'id': 'mortar_board'}))
        self.assertIn('👍🏽', render_icon({'type': 'emoji', 'id': '+1', 'skin': 4}))
        svg = render_icon({'type': 'tabler-icon', 'id': 'PacmanFilled', 'color': '#f2be00'})
        self.assertIn('<svg', svg)
        self.assertIn('page-icon', svg)
        self.assertIn('#f2be00', svg)
        self.assertNotIn('style=', svg)
        self.assertEqual(render_icon({'type': 'emoji', 'id': '<script>'}), '')
        self.assertEqual(render_icon({'type': 'svg', 'id': '<svg onload="evil()">'}), '')
        svg = render_icon({'type': 'tabler-icon', 'id': 'Book', 'color': '" onload="evil()'})
        self.assertNotIn('evil', svg)

    def test_icons_are_visible_in_titles_navigation_and_page_lists(self):
        self.nodes[1]['logseq.property/icon'] = {'type': 'emoji', 'id': 'mortar_board'}
        self.config['navigation'] = ['Home']
        g = Garden(self.nodes, self.source, self.config)
        self.assertIn('🎓', g.page_list([1]))
        self.assertIn('🎓', g.md.render('[[Home]]'))
        html = g.shell('Home', '', '/', '/s.css', '/s.js', home=True)
        self.assertEqual(html.count('🎓'), 3)  # desktop, mobile Explore, heading

    def test_directory_groups_accents_numbers_non_latin_and_escapes_titles(self):
        for eid, title in enumerate(['éclair', 'Alpha <script>', '9 lives', '日本語', 'zebra'], 2):
            self.nodes[eid] = node(title, str(eid), **{'block/name': title})
        g = Garden(self.nodes, self.source, self.config)
        html = g.page_directory()
        ids = [attrs['id'] for tag, attrs in Tags(html).tags if tag == 'section']
        self.assertEqual(ids, ['letter-other', 'letter-A', 'letter-E', 'letter-H', 'letter-Z'])
        self.assertEqual(html.count('<li>'), len(g.pages))
        self.assertNotIn('<script>', html)
        self.assertIn('href="#letter-E"', html)
        self.assertNotIn('href="#letter-Q"', html)

    def test_quiet_copy_is_publisher_specific_and_journals_have_a_style_hook(self):
        self.nodes[1]['block/journal-day'] = 20261021
        g = Garden(self.nodes, self.source, self.config)
        defaults = g.shell('Home', '', '/', '/s.css', '/s.js', home=True)
        self.assertIn('Always growing', defaults)
        self.config['decorative_copy'] = False
        quiet = g.shell('Home', '', '/', '/s.css', '/s.js', home=True)
        for text in ['Always growing', 'PERSONAL CORNER', 'Made of curiosity', 'portfolio & digital garden']:
            self.assertNotIn(text, quiet)
        self.assertIn('class="home journal"', quiet)

    def test_publisher_css_and_fonts_ship_without_changing_security_policy(self):
        source = self.source / 'publisher'
        shutil.copytree(HERE.parent / 'examples/minimal', source)
        (source / 'theme').mkdir()
        (source / 'theme/style.css').write_text(':root{--bg:#15131f}')
        (source / 'theme/body.woff2').write_bytes(b'font fixture')
        (source / 'theme/unsafe.js').write_text('throw new Error()')
        output = self.source / 'output'
        build(source, output, json.loads((source / 'site.json').read_text()))
        self.assertIn('--bg:#15131f', next((output / 'site').glob('garden-*.css')).read_text())
        self.assertEqual((output / 'theme/body.woff2').read_bytes(), b'font fixture')
        self.assertFalse((output / 'theme/unsafe.js').exists())
        global_policy = (output / '_headers').read_text().split('\n\n')[0]
        self.assertNotIn("'unsafe-inline'", global_policy)
        self.assertIn("font-src 'self'", global_policy)


if __name__ == '__main__':
    unittest.main()
