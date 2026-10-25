import pytest

from config_manager import ConfigManager
from providers.web import parse_search_flag
from search_engine import SearchEngine


@pytest.fixture
def config(tmp_path):
    return ConfigManager(config_dir=tmp_path)


@pytest.fixture
def engine(config):
    return SearchEngine(config)


def test_provider_map_registration(engine):
    expected_categories = [
        "Web",
        "Apps",
        "Files",
        "Clipboard",
        "Emoji",
        "Settings",
        "Time",
        "Units",
        "Commands",
        "Weather",
    ]
    for cat in expected_categories:
        assert cat in engine._provider_map
        assert len(engine._provider_map[cat]) >= 1


def test_search_flag_parser():
    res = parse_search_flag("-g python 3.12")
    assert res is not None
    flag, query, engine = res
    assert flag == "-g"
    assert query == "python 3.12"
    assert engine["key"] == "google"

    res_ya = parse_search_flag("-ya погода")
    assert res_ya is not None
    assert res_ya[0] == "-ya"
    assert res_ya[1] == "погода"
    assert res_ya[2]["key"] == "yandex"

    res_ddg = parse_search_flag("-ddg rust tutorial")
    assert res_ddg is not None
    assert res_ddg[0] == "-ddg"
    assert res_ddg[1] == "rust tutorial"
    assert res_ddg[2]["key"] == "duckduckgo"

    assert parse_search_flag("normal query without flag") is None


def test_category_routing_isolation(engine):
    # Empty query in specific category must route only to that category provider
    for cat in ["Apps", "Clipboard", "Emoji", "Time", "Commands", "Weather"]:
        providers = engine._provider_map.get(cat, [])
        assert len(providers) > 0
        for prov in providers:
            res = prov.search("", limit=5, category_filter=cat)
            assert isinstance(res, list)


def test_search_engine_stale_search_cancellation(engine):
    first_id = engine._current_search_id
    engine.search_async("query 1")
    second_id = engine._current_search_id
    assert second_id > first_id

    engine.search_async("query 2")
    third_id = engine._current_search_id
    assert third_id > second_id


def test_get_result_category_group():
    from providers.base import SearchResult
    from search_engine import get_result_category_group

    r_calc = SearchResult("math_1", "4", "2+2", "", 10.0, "Math", "CalculatorProvider")
    r_unit = SearchResult("unit_1", "100 cm", "1 m", "", 10.0, "Units", "UnitProvider")
    r_cur = SearchResult("cur_1", "100 USD", "", "", 10.0, "Currency", "CurrencyProvider")
    r_tz = SearchResult("tz_1", "12:00", "", "", 10.0, "Time", "TimezoneProvider")
    r_cmd = SearchResult("cmd_1", "Lock", "", "", 10.0, "Commands", "CommandProvider")
    r_wea = SearchResult("wea_1", "+20", "", "", 10.0, "Weather", "WeatherProvider")
    for r in [r_calc, r_unit, r_cur, r_tz, r_cmd, r_wea]:
        assert get_result_category_group(r) == "instant"

    r_app = SearchResult("app_1", "Terminal", "", "", 10.0, "Apps", "AppProvider")
    r_sett = SearchResult("set_1", "Settings", "", "", 10.0, "Settings", "AppProvider")
    assert get_result_category_group(r_app) == "apps"
    assert get_result_category_group(r_sett) == "apps"

    r_file = SearchResult("file_1", "notes.txt", "", "", 10.0, "Files", "FileProvider")
    assert get_result_category_group(r_file) == "files"

    r_clip = SearchResult("clip_1", "copied snippet", "", "", 10.0, "Clipboard", "ClipboardProvider")
    assert get_result_category_group(r_clip) == "clipboard"

    r_emoji = SearchResult("emo_1", "Smile", "", "", 10.0, "Emoji", "EmojiProvider")
    assert get_result_category_group(r_emoji) == "emoji"

    r_web = SearchResult("web_1", "Search Google", "", "", 10.0, "Web", "WebSearchProvider")
    assert get_result_category_group(r_web) == "web"


def test_group_and_sort_results_default_order(engine):
    from providers.base import SearchResult
    from search_engine import get_result_category_group

    r_emoji = SearchResult("emo_1", "Cat", "", "", 9.0, "Emoji", "EmojiProvider")
    r_clip = SearchResult("clip_1", "Text", "", "", 9.5, "Clipboard", "ClipboardProvider")
    r_file = SearchResult("file_1", "Doc.pdf", "", "", 8.0, "Files", "FileProvider")
    r_app = SearchResult("app_1", "Browser", "", "", 7.0, "Apps", "AppProvider")
    r_instant = SearchResult("math_1", "42", "", "", 10.0, "Math", "CalculatorProvider")
    r_web = SearchResult("web_1", "Web result", "", "", 6.0, "Web", "WebSearchProvider")

    input_results = [r_emoji, r_clip, r_file, r_app, r_instant, r_web]
    ordered = engine.group_and_sort_results(input_results, limit=10, is_global=True)

    ordered_groups = [get_result_category_group(r) for r in ordered]
    # Expected order: instant -> apps -> files -> clipboard -> emoji -> web
    assert ordered_groups == ["instant", "apps", "files", "clipboard", "emoji", "web"]
    # Verify clipboard is specifically after files and before emoji
    assert ordered_groups.index("files") < ordered_groups.index("clipboard") < ordered_groups.index("emoji")


def test_group_and_sort_results_custom_order(engine):
    from providers.base import SearchResult
    from search_engine import get_result_category_group

    r_emoji = SearchResult("emo_1", "Cat", "", "", 9.0, "Emoji", "EmojiProvider")
    r_clip = SearchResult("clip_1", "Text", "", "", 9.5, "Clipboard", "ClipboardProvider")
    r_file = SearchResult("file_1", "Doc.pdf", "", "", 8.0, "Files", "FileProvider")
    r_app = SearchResult("app_1", "Browser", "", "", 7.0, "Apps", "AppProvider")

    engine.config_manager.set("results_category_order", ["emoji", "clipboard", "files", "apps"])

    ordered = engine.group_and_sort_results([r_app, r_file, r_clip, r_emoji], limit=10, is_global=True)
    ordered_groups = [get_result_category_group(r) for r in ordered]
    assert ordered_groups == ["emoji", "clipboard", "files", "apps"]


def test_group_and_sort_results_disabled(engine):
    from providers.base import SearchResult

    r1 = SearchResult("emo_1", "Cat", "", "", 2.0, "Emoji", "EmojiProvider")
    r2 = SearchResult("file_1", "Doc.pdf", "", "", 9.0, "Files", "FileProvider")
    r3 = SearchResult("app_1", "Browser", "", "", 5.0, "Apps", "AppProvider")

    engine.config_manager.set("group_results_by_category", False)
    ordered = engine.group_and_sort_results([r1, r2, r3], limit=10, is_global=True)

    assert ordered[0].id == "file_1"
    assert ordered[1].id == "app_1"
    assert ordered[2].id == "emo_1"


def test_group_and_sort_results_single_category_limit(engine):
    from providers.base import SearchResult

    results = [
        SearchResult(f"app_{i}", f"App {i}", "", "", float(100 - i), "Apps", "AppProvider")
        for i in range(12)
    ]
    ordered = engine.group_and_sort_results(results, limit=10, is_global=True)
    assert len(ordered) == 10

