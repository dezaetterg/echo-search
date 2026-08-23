import os
import json
from .base import BaseProvider, SearchResult

class EmojiProvider(BaseProvider):
    def __init__(self, history_manager):
        super().__init__(history_manager)
        self.emojis = []
        self._load_db()

    def _load_db(self):
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'emoji.json')
            if not os.path.exists(db_path):
                system_db = "/usr/share/echo-search/emoji.json"
                if os.path.exists(system_db):
                    db_path = system_db
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        char = item.get("emoji")
                        if not char:
                            continue
                        name = item.get("description", "")
                        category = item.get("category", "Other")
                        aliases = item.get("aliases", [])
                        tags = item.get("tags", [])
                        keywords = set(aliases + tags)
                        self.emojis.append({
                            "char": char,
                            "name": name,
                            "category": category,
                            "kw": list(keywords)
                        })
        except Exception as e:
            print("Failed to load emoji DB:", e)
            
        self._load_characters()

    def _load_characters(self):
        chars = [
            ("±", "Plus-Minus Sign", ["math", "plus", "minus"]),
            ("×", "Multiplication Sign", ["math", "multiply", "times"]),
            ("÷", "Division Sign", ["math", "divide"]),
            ("∞", "Infinity", ["math", "infinity", "limit"]),
            ("≈", "Almost Equal To", ["math", "approximate", "equal"]),
            ("≠", "Not Equal To", ["math", "not equal"]),
            ("≤", "Less-Than or Equal To", ["math", "less"]),
            ("≥", "Greater-Than or Equal To", ["math", "greater"]),
            ("√", "Square Root", ["math", "root", "square"]),
            ("∑", "N-Ary Summation", ["math", "sum", "sigma"]),
            ("∫", "Integral", ["math", "integral"]),
            ("π", "Pi", ["math", "pi"]),
            ("€", "Euro Sign", ["currency", "euro", "money"]),
            ("£", "Pound Sign", ["currency", "pound", "money"]),
            ("¥", "Yen Sign", ["currency", "yen", "money"]),
            ("¢", "Cent Sign", ["currency", "cent", "money"]),
            ("₽", "Ruble Sign", ["currency", "ruble", "money"]),
            ("©", "Copyright Sign", ["symbol", "copyright", "law"]),
            ("®", "Registered Sign", ["symbol", "registered", "trademark"]),
            ("™", "Trade Mark Sign", ["symbol", "trademark"]),
            ("°", "Degree Sign", ["symbol", "degree", "temperature"]),
            ("•", "Bullet", ["symbol", "bullet", "point"]),
            ("§", "Section Sign", ["symbol", "section"]),
            ("¶", "Pilcrow Sign", ["symbol", "paragraph"]),
            ("†", "Dagger", ["symbol", "dagger"]),
            ("‡", "Double Dagger", ["symbol", "dagger", "double"]),
            ("✓", "Check Mark", ["symbol", "check", "tick", "yes"]),
            ("✗", "Ballot X", ["symbol", "cross", "no"]),
            ("←", "Leftwards Arrow", ["arrow", "left"]),
            ("↑", "Upwards Arrow", ["arrow", "up"]),
            ("→", "Rightwards Arrow", ["arrow", "right"]),
            ("↓", "Downwards Arrow", ["arrow", "down"]),
            ("↔", "Left Right Arrow", ["arrow", "left", "right"]),
            ("↵", "Downwards Arrow with Corner Leftwards", ["arrow", "return", "enter"])
        ]
        for char, name, tags in chars:
            self.emojis.append({
                "char": char,
                "name": name,
                "category": "Characters",
                "kw": tags
            })
            
    def _create_result(self, emoji_char: str, name: str, keywords: list, category: str, score: float) -> SearchResult:
        def _copy_callback():
            try:
                import gi
                gi.require_version('Gtk', '4.0')
                from gi.repository import Gdk
                clipboard = Gdk.Display.get_default().get_clipboard()
                clipboard.set(emoji_char)
            except: pass

        # Limit keywords string length for subtitle
        subtitle = ", ".join(keywords)
        if len(subtitle) > 60:
            subtitle = subtitle[:57] + "..."

        # Calculate Unicode (e.g. U+1F600)
        unicode_code = " ".join([f"U+{ord(c):04X}" for c in emoji_char])
        
        def _copy_unicode_callback():
            try:
                import gi
                gi.require_version('Gtk', '4.0')
                from gi.repository import Gdk
                clipboard = Gdk.Display.get_default().get_clipboard()
                clipboard.set(unicode_code)
            except: pass

        return SearchResult(
            id=f"emoji_{emoji_char}",
            title=f"{name}",
            subtitle=subtitle,
            icon=emoji_char, # We use icon to pass the character to the UI
            score=score,
            category="Emoji",
            provider="EmojiProvider",
            preview_data={"char": emoji_char, "name": name, "keywords": keywords, "emoji_category": category, "unicode_code": unicode_code},
            action_execute=_copy_callback,
            action_copy=_copy_callback,
            action_open_location=_copy_unicode_callback
        )

    def search(self, query: str, limit: int = 40, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Emoji"):
            return []
            
        q = query.lower().strip()
        
        if category_filter == "Emoji" and not q:
            # Return ALL emojis if no query
            return [self._create_result(em["char"], em["name"], em["kw"], em["category"], 100) for em in self.emojis]
            
        if not q or len(q) < 2:
            return []
            
        results = []
        for em in self.emojis:
            score = 0
            name_lower = em["name"].lower()
            if q == name_lower:
                score = 100
            elif q in name_lower:
                score = 80
            else:
                for kw in em["kw"]:
                    if q == kw.lower():
                        score = 90
                        break
                    elif q in kw.lower():
                        score = 70
                        break
                    
            if score > 0:
                results.append(self._create_result(em["char"], em["name"], em["kw"], em["category"], score))
                
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
