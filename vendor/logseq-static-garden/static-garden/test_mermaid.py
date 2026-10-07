"""Mermaid renderer macros: source extraction, fallbacks, escaping, and CSP scoping."""
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from build import Garden, HEADERS, HERE, csp, headers_text, mermaid_source


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class FakeGarden:
    """headers_text only needs urls, home, and diagram_pages."""
    def __init__(self, diagram_pages, home):
        self.diagram_pages = diagram_pages
        self.home = home
        self.urls = {1: '/', 2: '/page/notes--2/', 3: '/page/other--3/'}


class MermaidTests(unittest.TestCase):
    def setUp(self):
        self.diagram = 'flowchart LR\n    Seed[Idea] --> Evergreen[Evergreen page]'
        self.nodes = {
            1: {'block/title': 'Home', 'block/name': 'home', 'block/uuid': '11111111-1111-4111-8111-000000000001'},
            2: {'block/title': '{{renderer :mermaid}}',
                'block/uuid': '22222222-2222-4222-8222-222222222222', 'block/page': 1, 'block/parent': 1},
            3: {'block/title': '```mermaid\n' + self.diagram + '\n```',
                'block/uuid': '33333333-3333-4333-8333-333333333333', 'block/page': 1, 'block/parent': 2},
        }
        self.g = self.garden()

    def garden(self):
        return Garden(self.nodes, Path('/tmp'), {'home_page': 'Home'})

    def test_renderer_block_renders_source_and_consumes_children(self):
        result = self.g.block(2)
        tags = Tags(result).tags
        figure, pre = next((a for t, a in tags if t == 'figure'), None), next((a for t, a in tags if t == 'pre'), None)
        self.assertEqual(figure and figure.get('class'), 'diagram')
        self.assertEqual(pre and pre.get('class'), 'mermaid-source')
        self.assertIn(escape(self.diagram), result)
        self.assertNotIn('```mermaid', result)
        self.assertNotIn('{{renderer', result)
        self.assertNotIn('<ul class="outline">', result)  # the source child is consumed, not re-rendered
        self.assertEqual(self.g.diagrams, 1)
        self.assertIn(3, self.g.rendered_ids)
        self.assertFalse(self.g.warnings)

    def test_bare_child_and_junk_children(self):
        self.nodes[3]['block/title'] = '\n    '
        self.nodes[4] = {'block/title': self.diagram, 'block/uuid': '44444444-4444-4444-8444-444444444444',
                         'block/page': 1, 'block/parent': 2}
        self.nodes[5] = {'block/title': '```mermaid\n\n```', 'block/uuid': '55555555-5555-4555-8555-555555555555',
                         'block/page': 1, 'block/parent': 2}
        self.g = self.garden()
        result = self.g.block(2)
        self.assertIn(escape(self.diagram), result)
        self.assertIn(4, self.g.rendered_ids)
        self.assertIn(5, self.g.rendered_ids)
        self.assertFalse(self.g.warnings)

    def test_bermaid_typo_and_spacing_both_render(self):
        for title in ('{{renderer :bermaid}}', '{{renderer:mermaid}}', ' {{renderer :mermaid}} '):
            with self.subTest(title=title):
                self.nodes[2]['block/title'] = title
                self.assertIn('mermaid-source', self.g.block(2))

    def test_other_renderer_ids_stay_source_with_warning(self):
        self.nodes[2]['block/title'] = '{{renderer :excalidraw}}'
        result = self.g.block(2)
        self.assertNotIn('mermaid-source', result)
        self.assertIn('<ul class="outline">', result)  # children render as normal blocks
        self.assertTrue(any('Macro/query retained as source' in w for w in self.g.warnings))

    def test_renderer_without_usable_source_warns(self):
        self.nodes[3]['block/title'] = '   '
        result = self.g.block(2)
        self.assertNotIn('mermaid-source', result)
        self.assertTrue(any('Macro/query retained as source' in w for w in self.g.warnings))

    def test_diagram_source_is_escaped(self):
        hostile = 'flowchart LR\n    A["<script>alert(1)</script>"] --> B'
        self.nodes[3]['block/title'] = '```mermaid\n' + hostile + '\n```'
        result = self.g.block(2)
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)

    def test_mermaid_source_directly(self):
        cases = [
            (['```mermaid\ngraph TD\n  A-->B\n```'], 'graph TD\n  A-->B'),
            (['```\ngraph TD\n  A-->B\n```'], 'graph TD\n  A-->B'),
            (['', '   ', '\n', 'graph TD\n  A-->B'], 'graph TD\n  A-->B'),
            (['```mermaid\n\n```', 'graph TD\n  A-->B'], 'graph TD\n  A-->B'),
            (['sequenceDiagram\n  A->>B: hi'], 'sequenceDiagram\n  A->>B: hi'),
        ]
        for titles, expected in cases:
            with self.subTest(titles=titles):
                self.assertEqual(mermaid_source(titles), expected)
        self.assertIsNone(mermaid_source(['', '  ', '```mermaid\n\n```']))

    def test_page_with_diagram_is_tracked_for_csp_scoping(self):
        self.g.current_page = 1
        self.g.block(2)
        self.assertEqual(self.g.diagram_pages, {1})


class HeaderScopingTests(unittest.TestCase):
    def test_no_diagrams_leaves_global_policy_strict(self):
        self.assertEqual(headers_text(FakeGarden(set(), 1)), HEADERS)
        self.assertIn("style-src 'self';", HEADERS)
        self.assertNotIn('unsafe-inline', HEADERS)

    def test_diagram_pages_get_detached_relaxed_rules(self):
        headers = headers_text(FakeGarden({2}, 1))
        self.assertIn('\n/page/notes--2/\n  ! Content-Security-Policy\n  Content-Security-Policy: ' + csp(inline_styles=True), headers)
        self.assertNotIn('/page/other--3/', headers)
        # The global rule keeps the strict policy; only the scoped rule relaxes it.
        global_rule = headers.split('\n\n')[0]
        self.assertIn(csp(), global_rule)
        self.assertNotIn('unsafe-inline', global_rule)

    def test_homepage_diagrams_relax_the_global_policy_instead(self):
        headers = headers_text(FakeGarden({1, 2}, 1))
        self.assertIn(csp(inline_styles=True), headers)
        self.assertNotIn('! Content-Security-Policy', headers)  # no scoped overrides
        self.assertNotIn(csp() + '\n', headers.split('\n\n')[0])  # strict policy gone


class BuildIntegrationTests(unittest.TestCase):
    def test_example_build_ships_diagram_assets_and_scoped_headers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'public export'
            shutil.copytree(HERE.parent / 'examples/minimal', source)
            output = root / 'website'
            result = subprocess.run([sys.executable, str(HERE / 'build.py'), '--output', str(output)],
                                    cwd=source, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root / 'website-report.json').read_text())
            # Once on the Notes page, once more inside the Projects page's embed.
            self.assertEqual(report['diagrams'], 2)
            self.assertEqual(report['warnings'], [])
            notes = next(output.glob('page/notes--*/index.html')).read_text()
            self.assertIn('<pre class="mermaid-source">', notes)
            self.assertIn('flowchart LR', notes)
            self.assertIn('<meta name="mermaid-src" content="/site/mermaid-', notes)
            home = (output / 'index.html').read_text()
            self.assertNotIn('mermaid-src', home)  # pages without diagrams load nothing
            bundled = list(output.glob('site/mermaid-*.js'))
            self.assertEqual(len(bundled), 1)
            self.assertGreater(bundled[0].stat().st_size, 1_000_000)
            headers = (output / '_headers').read_text()
            self.assertIn('! Content-Security-Policy', headers)
            self.assertIn("'unsafe-inline'", headers)


if __name__ == '__main__':
    unittest.main()
