"""Search provided 500 Tabler SVG icons by ID/name/Chinese semantic word."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'icon_library'

class IconLibrary:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.items = json.loads((self.root / 'INDEX/icon_manifest.json').read_text(encoding='utf-8'))
        self.by_id = {item['id'].lower(): item for item in self.items}
        self.by_name = {item['source_icon_name'].lower(): item for item in self.items}
        self.semantic = json.loads((self.root / 'INDEX/semantic_index_zh.json').read_text(encoding='utf-8'))
        self.aliases = json.loads((self.root / 'INDEX/aliases_zh.json').read_text(encoding='utf-8'))

    def search(self, phrase, limit=8):
        key = str(phrase).strip()
        if not key: return []
        exact = self.by_id.get(key.lower()) or self.by_name.get(key.lower())
        if exact: return [exact]
        normalized = self.aliases.get(key, key)
        ranked = {}
        def add(item, score):
            if item: ranked[item['id']] = max(ranked.get(item['id'], 0), score)
        for id_ in self.semantic.get(normalized, []) + self.semantic.get(key, []):
            add(self.by_id.get(id_.lower()), 120)
        for item in self.items:
            if key in (item.get('keywords_zh') or []) or key == item.get('name_zh'): add(item, 110)
            if normalized in (item.get('keywords_zh') or []): add(item, 100)
            if key.lower() in item.get('name_en','').lower(): add(item, 60)
            if key in item.get('name_zh','') or normalized in item.get('name_zh',''): add(item, 50)
            if key in ' '.join(item.get('keywords_zh') or []): add(item, 20)
        return sorted((self.by_id[id_.lower()] for id_ in ranked), key=lambda a:(-ranked[a['id']], a.get('priority','P9'), -a.get('selection_score_total',0)))[:limit]

    def path(self, term):
        matches=self.search(term, 1)
        if not matches: raise ValueError(f'图标库找不到: {term}; 使用 python run_workflow.py search-icon "关键词" 查看候选')
        rel=Path(matches[0]['relative_path'])
        path=(self.root / rel).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file(): raise ValueError(f'错误图标路径: {rel}')
        return path, matches[0]
