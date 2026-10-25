import os

import pytest

from i18n import i18n, t
from preview_manager import APP_CAT_I18N, EMOJI_CAT_KEYS, PreviewManager
from providers.base import SearchResult
from providers.files import FileProvider


def test_app_category_localization():
    i18n.set_language('ru')
    res_ru = SearchResult(
        id='test-app',
        title='Code Editor',
        subtitle='Application',
        icon='text-editor',
        score=100.0,
        category='Apps',
        provider='AppProvider',
        preview_data={
            'type': 'app',
            'categories': 'Development;IDE;Utility;',
        }
    )
    widget_ru = PreviewManager.render(res_ru)
    assert widget_ru is not None
    assert t(APP_CAT_I18N['development']) == 'Разработка'
    assert t(APP_CAT_I18N['utility']) == 'Утилиты'

    i18n.set_language('en')
    assert t(APP_CAT_I18N['development']) == 'Development'
    assert t(APP_CAT_I18N['utility']) == 'Utilities'
    widget_en = PreviewManager.render(res_ru)
    assert widget_en is not None
    i18n.set_language('ru')

def test_emoji_category_localization():
    i18n.set_language('ru')
    res_emoji = SearchResult(
        id='test-emoji',
        title='Grinning Face',
        subtitle='Emoji',
        icon='face-smile',
        score=100.0,
        category='Emoji',
        provider='EmojiProvider',
        preview_data={
            'char': '😀',
            'emoji_category': 'Smileys & Emotion',
            'unicode_code': 'U+1F600',
        }
    )
    widget_ru = PreviewManager.render(res_emoji)
    assert widget_ru is not None
    assert t(EMOJI_CAT_KEYS['Smileys & Emotion']) == 'Смайлы и эмоции'
    assert t(EMOJI_CAT_KEYS['Animals & Nature']) == 'Животные и природа'

    i18n.set_language('en')
    assert t(EMOJI_CAT_KEYS['Smileys & Emotion']) == 'Smileys & Emotion'
    assert t(EMOJI_CAT_KEYS['Animals & Nature']) == 'Animals & Nature'
    i18n.set_language('ru')

def test_file_size_localization():
    provider = FileProvider(history_manager=None)
    
    i18n.set_language('ru')
    size_mb_ru = provider._format_size(1024 * 1024 * 5)
    assert 'МБ' in size_mb_ru
    size_kb_ru = provider._format_size(1024 * 50)
    assert 'КБ' in size_kb_ru
    size_gb_ru = provider._format_size(1024 * 1024 * 1024 * 2)
    assert 'ГБ' in size_gb_ru

    i18n.set_language('en')
    size_mb_en = provider._format_size(1024 * 1024 * 5)
    assert 'MB' in size_mb_en
    size_kb_en = provider._format_size(1024 * 50)
    assert 'KB' in size_kb_en
    size_gb_en = provider._format_size(1024 * 1024 * 1024 * 2)
    assert 'GB' in size_gb_en
    
    i18n.set_language('ru')


def test_placeholders_and_file_hints_localization():
    i18n.set_language('ru')
    assert t('apps_placeholder') == 'Приложения'
    assert t('files_placeholder') == 'Файлы'
    assert t('emoji_placeholder') == 'Поиск эмодзи'
    assert t('section_recent') == 'Недавние файлы'
    assert 'быстрого просмотра файла' in t('files_quick_look_hint', key='[Пробел]')

    i18n.set_language('en')
    assert t('apps_placeholder') == 'Applications'
    assert t('files_placeholder') == 'Files'
    assert t('emoji_placeholder') == 'Emoji Search'
    assert t('section_recent') == 'Recent Files'
    assert 'file Quick Look' in t('files_quick_look_hint', key='[Space]')
    i18n.set_language('ru')


def test_weather_strings_and_summaries_localization():
    i18n.set_language('ru')
    assert t('weather_mode_conditions') == 'Погодные условия'
    summary = t('weather_summary_clear_night', gust=22)
    assert 'Порывы ветра до 22 км/ч. Ясно до утра.' == summary

    i18n.set_language('en')
    assert t('weather_mode_conditions') == 'Conditions'
    assert 'Wind gusts up to 22 km/h. Clear until morning.' == t('weather_summary_clear_night', gust=22)
    i18n.set_language('ru')


def test_emoji_ru_dictionary_and_provider():
    from providers.emoji import EmojiProvider
    from providers.emoji_ru import get_emoji_ru_name

    assert get_emoji_ru_name('😀', 'grinning face') == 'Улыбка'
    assert get_emoji_ru_name('🙃', 'upside-down face') == 'Вверх ногами'
    assert get_emoji_ru_name('🫠', 'melting face') == 'Тающее лицо'
    assert get_emoji_ru_name('🤣', 'rolling on the floor laughing') == 'Катаюсь от смеха'

    i18n.set_language('ru')
    provider = EmojiProvider(history_manager=None)
    res = provider.search('', category_filter='Emoji')
    assert len(res) > 100
    first = res[0]
    assert first.preview_data.get('name_ru') == 'Улыбка'
    assert 'Улыбка' in first.title


def test_weather_detailed_mode_all_13_languages():
    from datetime import datetime

    from i18n import SUPPORTED_LANGUAGES
    from providers.weather import WEEKDAY_LETTERS, format_full_date, get_smart_day_summary

    assert len(SUPPORTED_LANGUAGES) == 13
    test_dt = datetime(2026, 9, 18, 14, 30)
    mock_day = {
        'code': 3,
        'temp': 23,
        'min': 19,
        'max': 28,
        'apparent_min': 17,
        'apparent_max': 28,
        'humidity': 70,
        'feels_like': 24,
        'wind_speed': 12,
        'precip_prob_max': 10
    }

    for lang in SUPPORTED_LANGUAGES:
        i18n.set_language(lang)
        # 1. Forecast title
        fc = t('weather_card_forecast')
        assert fc != 'weather_card_forecast', f'Missing forecast title for {lang}'
        assert len(fc) > 0

        # 2. format_full_date
        fdate = format_full_date(test_dt, lang=lang)
        assert len(fdate) > 5, f'Bad full date for {lang}: {fdate}'

        # 3. WEEKDAY_LETTERS
        letters = WEEKDAY_LETTERS.get(lang)
        assert letters is not None, f'Missing weekday letters for {lang}'
        assert len(letters) == 7, f'Letters length != 7 for {lang}'
        for letter in letters:
            assert len(letter) == 1, f'Weekday letter length != 1 for {lang}: {letter}'
            if lang not in ('zh', 'ja', 'ar'):
                assert letter.isupper(), f'Weekday letter is not uppercase for {lang}: {letter}'

        # 4. Weather summary under graph
        summary = get_smart_day_summary(mock_day, lang=lang, is_today=True, temp_unit='celsius', current_temp=23)
        eod = t('weather_cond_summary_end_of_day', temp=23, min=19)
        full_summary = f"{summary} {eod}"
        assert 'weather_' not in full_summary, f'Uninterpolated key in {lang}: {full_summary}'
        if lang != 'en':
            assert 'Temperature through end of day' not in full_summary

    i18n.set_language('ru')

