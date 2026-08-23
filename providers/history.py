import os
import json
import time

class HistoryManager:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.history_file = os.path.expanduser("~/.local/share/echo/history.json")
        self.usage_data = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.usage_data = json.load(f)
                    
                    # Миграция старых форматов
                    for k, v in list(self.usage_data.items()):
                        if isinstance(v, int):
                            self.usage_data[k] = {'count': v, 'last_used': time.time(), 'queries': {}}
                        elif isinstance(v, dict) and 'queries' not in v:
                            v['queries'] = {}
        except:
            self.usage_data = {}

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.usage_data, f)
        except:
            pass

    def record_launch(self, app_id: str, query: str = ""):
        search_history = self.config_manager.get("search_history") if self.config_manager else True
        if not search_history or not app_id: return
        if app_id not in self.usage_data:
            self.usage_data[app_id] = {'count': 0, 'last_used': 0, 'queries': {}}
            
        self.usage_data[app_id]['count'] += 1
        self.usage_data[app_id]['last_used'] = time.time()
        
        q = query.lower().strip()
        if q:
            queries = self.usage_data[app_id].get('queries', {})
            queries[q] = queries.get(q, 0) + 1
            self.usage_data[app_id]['queries'] = queries
            
        self.save()

    def get_score_bonus(self, app_id: str, current_query: str = "") -> float:
        search_history = self.config_manager.get("search_history") if self.config_manager else True
        if not search_history: return 0.0
        
        data = self.usage_data.get(app_id)
        if not data: return 0.0
        
        days_since = (time.time() - data.get('last_used', 0)) / 86400.0
        
        # Частые запуски (макс 15 баллов)
        freq_bonus = min(15.0, data.get('count', 0) * 1.5)
        
        # Совпадение запроса (макс 25 баллов)
        query_bonus = 0.0
        q = current_query.lower().strip()
        if q and 'queries' in data:
            query_count = data['queries'].get(q, 0)
            query_bonus = min(25.0, query_count * 5.0)
            
        total_bonus = freq_bonus + query_bonus
        
        # Decay: теряем 0.5 балла за каждый день простоя
        decay_penalty = days_since * 0.5
        
        final_bonus = max(0.0, total_bonus - decay_penalty)
        return min(30.0, final_bonus)

    def get_recent_apps(self, limit=10):
        search_history = self.config_manager.get("search_history") if self.config_manager else True
        if not search_history: return []
        
        sorted_items = sorted(
            self.usage_data.items(), 
            key=lambda x: (x[1]['last_used'], x[1]['count']), 
            reverse=True
        )
        return [k for k, v in sorted_items[:limit]]
