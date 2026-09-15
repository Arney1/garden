"""Read the Transit JSON subset emitted by Logseq's Datascript exporter."""
import json
from dataclasses import dataclass

@dataclass
class Tagged:
    tag: str
    value: object

class Reader:
    def __init__(self):
        self.cache = []
        self.index = 0

    def string(self, s, key=False):
        if s.startswith('^') and s != '^ ':
            code = s[1:]
            index = 0
            for c in code:
                index = index * 44 + ord(c) - 48
            return self.cache[index]
        cacheable = len(s) > 3 and (key or s.startswith(('~:', '~$', '~#')))
        if s.startswith(('~:', '~$', '~u')):
            value = s[2:]
        elif s.startswith('~i'):
            value = int(s[2:])
        elif s.startswith(('~~', '~^', '~`')):
            value = s[1:]
        elif s.startswith('~#'):
            value = Tagged(s[2:], None)
        elif s.startswith('~'):
            raise ValueError(f'Unsupported Transit scalar {s[:100]!r}')
        else:
            value = s
        if cacheable:
            if self.index == 1936:
                self.index = 0
            if self.index < len(self.cache):
                self.cache[self.index] = value
            else:
                self.cache.append(value)
            self.index += 1
        return value

    def read(self, value, key=False):
        if isinstance(value, str):
            return self.string(value, key)
        if isinstance(value, dict):
            return {self.read(k, True): self.read(v) for k, v in value.items()}
        if not isinstance(value, list):
            return value
        if value and value[0] == '^ ':
            return {self.read(value[i], True): self.read(value[i+1]) for i in range(1, len(value), 2)}
        if not value:
            return []
        first = self.read(value[0])
        if isinstance(first, Tagged) and first.value is None:
            rep = self.read(value[1])
            if first.tag in ('set', 'list'):
                return rep
            if first.tag in ('datascript/DB', 'datascript/Datom'):
                return Tagged(first.tag, rep)
            raise ValueError(f'Unsupported Transit tag {first.tag}')
        return [first] + [self.read(v) for v in value[1:]]

def load_export(path):
    source = path.read_text(encoding='utf-8')
    marker = 'window.logseq_db='
    if marker not in source:
        raise ValueError(f'{path} is not a Logseq public-pages export')
    raw, _ = json.JSONDecoder().raw_decode(source.split(marker, 1)[1])
    for code, character in [('amp', '&'), ('lt', '<'), ('gt', '>'), ('quot', '"'), ('apos', "'")]:
        raw = raw.replace('logseq____&' + code + ';', character)
    db = Reader().read(json.loads(raw))
    if not isinstance(db, Tagged) or db.tag != 'datascript/DB':
        raise ValueError('Expected a Datascript database')
    return db.value
