"""YouTube macro rendering and frame-origin restrictions."""
from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import parse_qs, urlsplit

from build import Garden, HEADERS, video_html


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.id = '0-zDFLbWK1Q'
        self.nodes = {
            1: {'block/title': 'Home', 'block/name': 'home', 'block/uuid': '11111111-1111-4111-8111-111111111111'},
            2: {'block/title': '{{video https://youtu.be/' + self.id + '}}',
                'block/uuid': '22222222-2222-4222-8222-222222222222', 'block/page': 1, 'block/parent': 1},
        }
        self.g = Garden(self.nodes, Path('/tmp'), {'home_page': 'Home'})

    def test_exported_macro_renders_player_and_fallback_without_source_warning(self):
        result = self.g.block(2)
        tags = Tags(result).tags
        frame = next(attrs for tag, attrs in tags if tag == 'iframe')
        self.assertEqual(frame['src'], 'https://www.youtube-nocookie.com/embed/' + self.id + '?playsinline=1')
        self.assertEqual(frame['loading'], 'lazy')
        self.assertEqual(frame['referrerpolicy'], 'strict-origin-when-cross-origin')
        self.assertIn('allowfullscreen', frame)
        self.assertTrue(any(tag == 'a' and attrs.get('href') == 'https://www.youtube.com/watch?v=' + self.id for tag, attrs in tags))
        self.assertNotIn('{{video', result)
        self.assertFalse(self.g.warnings)
        self.assertIn(2, self.g.rendered_ids)

    def test_supported_urls_and_timestamps_are_normalized(self):
        cases = [
            ('https://youtu.be/' + self.id + '?t=15', '15'),
            ('https://www.youtube.com/watch?v=' + self.id + '&t=1m30s&autoplay=1', '90'),
            ('https://m.youtube.com/watch?v=' + self.id + '&amp;start=30', '30'),
            ('https://youtube.com/shorts/' + self.id, None),
            ('https://youtube.com/live/' + self.id, None),
            ('https://www.youtube-nocookie.com/embed/' + self.id + '#t=1h2m3s', '3723'),
            ('[video](https://youtu.be/' + self.id + ')', None),
            ('<https://youtu.be/' + self.id + '>', None),
        ]
        for raw, start in cases:
            with self.subTest(raw=raw):
                frame = next(attrs for tag, attrs in Tags(video_html('{{video ' + raw + '}}')).tags if tag == 'iframe')
                parts = urlsplit(frame['src'])
                self.assertEqual(parts.netloc, 'www.youtube-nocookie.com')
                self.assertEqual(parts.path, '/embed/' + self.id)
                query = parse_qs(parts.query)
                self.assertEqual(query.get('start', [None])[0], start)
                self.assertNotIn('autoplay', query)

    def test_untrusted_hosts_schemes_and_markup_never_become_frames(self):
        for raw in ('javascript:alert(1)', 'https://youtube.com.evil.invalid/watch?v=' + self.id,
                    'https://youtube.com@evil.invalid/watch?v=' + self.id,
                    'https://evil.invalid/embed/' + self.id, 'https://youtu.be/invalid',
                    'https://youtu.be/' + self.id + '" onload="alert(1)',
                    'https://www.youtube.com/watch?v=%22%3E%3Cscript%3E',
                    'https://www.youtube.com:444/watch?v=' + self.id):
            with self.subTest(raw=raw):
                self.nodes[2]['block/title'] = '{{video ' + raw + '}}'
                tags = Tags(self.g.block(2)).tags
                self.assertFalse(any(tag in ('iframe', 'script', 'object') for tag, _ in tags))
                self.assertFalse(any(key.startswith('on') for _, attrs in tags for key in attrs))
        self.assertTrue(self.g.warnings)

    def test_code_examples_are_not_embedded(self):
        original = self.nodes[2]['block/title']
        for text in ('`' + original + '`', '```text\n' + original + '\n```'):
            self.nodes[2]['block/title'] = text
            self.assertNotIn('<iframe', self.g.block(2))
        self.nodes[2]['block/title'] = original
        for display in ('code', 'math'):
            self.nodes[2]['logseq.property.node/display-type'] = display
            self.assertNotIn('<iframe', self.g.block(2))

    def test_heading_metadata_does_not_replace_video_with_macro_text(self):
        self.nodes[2]['logseq.property/heading'] = 2
        self.assertIn('<iframe', self.g.block(2))
        self.assertNotIn('{{video', self.g.block(2))

    def test_frame_policy_allows_only_the_generated_provider(self):
        global_rules = HEADERS.split('\n\n')[0]
        directive = next(part.strip() for part in global_rules.split(';') if part.strip().startswith('frame-src '))
        self.assertEqual(directive, 'frame-src https://www.youtube-nocookie.com')
        self.assertIn("frame-ancestors 'none'", global_rules)
        self.assertIn('X-Frame-Options: DENY', global_rules)


if __name__ == '__main__':
    unittest.main()
