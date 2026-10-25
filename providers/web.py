"""Web search and terminal integration provider for Echo Search."""
import os
import shutil
import subprocess
import urllib.parse
from typing import List, Optional, Tuple

from gi.repository import Gio

from i18n import t
from logger import get_logger
from providers.base import BaseProvider, SearchResult

logger = get_logger("web")

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_WEB_ICONS_DIR = os.path.abspath(os.path.join(_BASE_DIR, '..', 'assets', 'icons', 'web'))


def get_engine_icon(engine_key: str) -> str:
    key = (engine_key or '').strip().lower()
    for icons_dir in (
        _WEB_ICONS_DIR,
        '/usr/share/echo-search/assets/icons/web',
        '/usr/lib/echo-search/assets/icons/web',
        os.path.expanduser('~/.local/share/echo-search/assets/icons/web'),
    ):
        svg_path = os.path.join(icons_dir, f'{key}.svg')
        if os.path.exists(svg_path):
            return svg_path
    return 'applications-internet-symbolic'


SEARCH_ENGINES = {
    'google': {
        'name': 'Google',
        'url': 'https://www.google.com/search?q={query}',
        'icon': 'google',
    },
    'yandex': {
        'name': 'Яндекс',
        'url': 'https://ya.ru/search/?text={query}',
        'icon': 'yandex',
    },
    'duckduckgo': {
        'name': 'DuckDuckGo',
        'url': 'https://duckduckgo.com/?q={query}',
        'icon': 'duckduckgo',
    },
    'brave': {
        'name': 'Brave',
        'url': 'https://search.brave.com/search?q={query}',
        'icon': 'brave',
    },
    'bing': {
        'name': 'Bing',
        'url': 'https://www.bing.com/search?q={query}',
        'icon': 'bing',
    },
    'youtube': {
        'name': 'YouTube',
        'url': 'https://www.youtube.com/results?search_query={query}',
        'icon': 'youtube',
    },
    'github': {
        'name': 'GitHub',
        'url': 'https://github.com/search?q={query}',
        'icon': 'github',
    },
    'wikipedia': {
        'name': 'Wikipedia',
        'url': 'https://wikipedia.org/w/index.php?search={query}',
        'icon': 'wikipedia',
    },
}

FLAG_MAPPINGS = {
    '-g': 'google',
    '-п': 'google',
    '!g': 'google',
    '-ya': 'yandex',
    '-я': 'yandex',
    '!ya': 'yandex',
    '-ddg': 'duckduckgo',
    '-ввг': 'duckduckgo',
    '!ddg': 'duckduckgo',
    '-b': 'brave',
    '-и': 'brave',
    '!b': 'brave',
    '-bing': 'bing',
    '!bing': 'bing',
    '-y': 'youtube',
    '-н': 'youtube',
    '!y': 'youtube',
    '-gh': 'github',
    '-гх': 'github',
    '!gh': 'github',
    '-w': 'wikipedia',
    '-ц': 'wikipedia',
    '!w': 'wikipedia',
}


def parse_search_flag(query: str) -> Optional[Tuple[str, str, dict]]:
    """
    Parses a query for quick search flags like -g, !g, -ya, -ddg, etc.
    Returns (flag, clean_query, engine_info) or None.
    """
    raw = query.strip()
    if not (raw.startswith('-') or raw.startswith('!')):
        return None

    parts = raw.split(maxsplit=1)
    flag = parts[0].lower()
    clean_query = parts[1].strip() if len(parts) > 1 else ''

    if flag in FLAG_MAPPINGS:
        engine_key = FLAG_MAPPINGS[flag]
        if engine_key in SEARCH_ENGINES:
            engine_info = SEARCH_ENGINES[engine_key].copy()
            engine_info['key'] = engine_key
            engine_info['icon'] = get_engine_icon(engine_key)
            return flag, clean_query, engine_info

    return None


def build_search_url(query: str, engine_key: str = 'google', custom_url: str = '') -> str:
    """Builds a search URL for the given query and engine."""
    encoded = urllib.parse.quote_plus(query.strip())
    if engine_key == 'custom' and custom_url:
        if '{query}' in custom_url:
            return custom_url.replace('{query}', encoded)
        return f'{custom_url}{encoded}'

    engine = SEARCH_ENGINES.get(engine_key, SEARCH_ENGINES['google'])
    return engine['url'].format(query=encoded)


def open_url_in_browser(url: str) -> bool:
    """Opens a URL in the user default browser."""
    try:
        if Gio.AppInfo.launch_default_for_uri(url, None):
            return True
    except Exception as e:
        logger.debug("Gio launch_default_for_uri failed for %s: %s", url, e)

    try:
        subprocess.Popen(['xdg-open', url])
        return True
    except Exception as e:
        logger.warning("xdg-open failed for %s: %s", url, e)
        return False


def open_in_terminal(command: str = '') -> bool:
    """
    Opens the default terminal emulator.
    If a command is provided, executes it in the user's default shell
    and keeps the interactive shell open after execution so output is visible.
    """
    cmd_str = (command or '').strip()
    user_shell = os.environ.get('SHELL') or '/bin/bash'

    if cmd_str:
        shell_script = f'{cmd_str}; exec {user_shell}'
    else:
        shell_script = ''

    # Candidates in order of desktop preference
    # (binary, args_without_command, args_with_command)
    candidates = [
        ('ptyxis', ['ptyxis'], ['ptyxis', '--', user_shell, '-c', shell_script]),
        ('xdg-terminal-exec', ['xdg-terminal-exec'], ['xdg-terminal-exec', user_shell, '-c', shell_script]),
        ('gnome-terminal', ['gnome-terminal'], ['gnome-terminal', '--', user_shell, '-c', shell_script]),
        ('konsole', ['konsole'], ['konsole', '-e', user_shell, '-c', shell_script]),
        ('xfce4-terminal', ['xfce4-terminal'], ['xfce4-terminal', '-x', user_shell, '-c', shell_script]),
        ('kitty', ['kitty'], ['kitty', user_shell, '-c', shell_script]),
        ('alacritty', ['alacritty'], ['alacritty', '-e', user_shell, '-c', shell_script]),
        ('foot', ['foot'], ['foot', user_shell, '-c', shell_script]),
        ('x-terminal-emulator', ['x-terminal-emulator'], ['x-terminal-emulator', '-e', user_shell, '-c', shell_script]),
    ]

    for term_bin, empty_args, exec_args in candidates:
        if shutil.which(term_bin):
            try:
                run_args = exec_args if cmd_str else empty_args
                subprocess.Popen(run_args)
                return True
            except Exception as e:
                logger.debug("Terminal launch failed for %s: %s", term_bin, e)
                continue

    return False


class WebSearchProvider(BaseProvider):
    """Provider that yields direct web search cards when search flags are detected."""

    def __init__(self, config_manager=None, history_manager=None):
        super().__init__(history_manager=history_manager)
        self.config_manager = config_manager

    def search(self, query: str, limit: int = 10, category_filter: str = None) -> List[SearchResult]:
        if not query:
            return []

        flags_enabled = True
        if self.config_manager:
            flags_enabled = self.config_manager.get('web_search_flags', True)

        if not flags_enabled:
            return []

        flag_info = parse_search_flag(query)
        if not flag_info:
            return []

        flag, clean_query, engine = flag_info
        engine_name = engine['name']
        engine_key = engine.get('key', 'google')
        icon_path = get_engine_icon(engine_key)

        if clean_query:
            title = f"{t('web_search_in', engine=engine_name)}: «{clean_query}»"
            subtitle = t('web_search_action_open')
            target_query = clean_query
        else:
            title = f"{t('web_search_in', engine=engine_name)} ({flag})"
            subtitle = t('web_search_type_query')
            target_query = ''

        def _execute():
            if target_query:
                url = engine['url'].format(query=urllib.parse.quote_plus(target_query))
            else:
                base_url = engine['url'].split('?')[0]
                url = base_url
            open_url_in_browser(url)

        res = SearchResult(
            id=f'web_flag_{flag}',
            title=title,
            subtitle=subtitle,
            icon=icon_path,
            score=9999.0,
            category='Web',
            provider='WebSearchProvider',
            preview_data={
                'engine': engine_name,
                'query': target_query,
                'flag': flag,
            },
            action_execute=_execute
        )
        return [res]
