# -*- coding: utf-8 -*-
"""Stable note identity and safe scalar parsing; no production writes on import."""
import pathlib, re, yaml
def frontmatter(path):
    text = pathlib.Path(path).read_text(encoding='utf-8-sig')
    m = re.match(r'\A---\r?\n(.*?)\r?\n---', text, re.S)
    if not m:
        raise ValueError('Missing frontmatter: ' + str(path))
    value = yaml.safe_load(m.group(1) + '\n') or {}
    if not isinstance(value, dict):
        raise ValueError('Invalid frontmatter mapping: ' + str(path))
    return value
_id_cache = {}

def stable_note_path(directory, object_id, default_name):
    matches = []
    for p in pathlib.Path(directory).glob('*.md'):
        stat = p.stat()
        signature = (stat.st_mtime_ns, stat.st_size)
        prior = _id_cache.get(str(p))
        if prior is None or prior[0] != signature:
            prior = (signature, frontmatter(p).get('id'))
            _id_cache[str(p)] = prior
        if prior[1] == object_id:
            matches.append(p)
    if len(matches) > 1:
        raise ValueError('Duplicate stable ID: ' + object_id)
    return str(matches[0] if matches else pathlib.Path(directory) / default_name)
