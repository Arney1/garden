"""Render Logseq icon metadata from trusted, offline icon registries."""
from functools import lru_cache
import gzip
from html import escape
import json
from pathlib import Path
import re


@lru_cache(maxsize=2)
def registry(name):
    path = Path(__file__).resolve().parent.parent / f'vendor/icons/{name}.json.gz'
    return json.loads(gzip.decompress(path.read_bytes()))


def render_icon(value):
    if not isinstance(value, dict) or not isinstance(value.get('id'), str):
        return ''
    ident = value['id']
    if value.get('type') == 'emoji':
        skins = registry('emoji-mart').get(ident)
        if not skins:
            return ''
        skin = value.get('skin', 1)
        index = skin - 1 if type(skin) is int and 1 <= skin <= len(skins) else 0
        return f'<span class="page-icon emoji" aria-hidden="true">{escape(skins[index])}</span>'
    if value.get('type') == 'tabler-icon':
        key = re.sub(r'[-_\s]', '', ident).casefold()
        svg = registry('tabler').get(key)
        if not svg:
            return ''
        # Only trusted registry markup is inserted, never graph-supplied SVG/HTML.
        color = value.get('color', '')
        color = color if isinstance(color, str) and re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', color) else 'currentColor'
        svg = svg.replace('currentColor', color)
        return svg.replace('<svg ', '<svg aria-hidden="true" ', 1).replace('class="', 'class="page-icon ', 1)
    return ''
