import os
import re
import json
import time
import urllib.request
import threading
from datetime import datetime
from .base import BaseProvider, SearchResult
from i18n import t, get_current_language

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gdk
except (ValueError, ImportError):
    pass

CURRENCY_ICON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons', 'currency-converter.svg')
)

FALLBACK_USD_VALUES = {
    'USD': 1.0,
    'EUR': 1.087,
    'RUB': 0.01162,
    'KZT': 0.00208,
    'BYN': 0.307,
    'CNY': 0.138,
    'GBP': 1.282,
    'JPY': 0.0068,
    'TRY': 0.0294,
    'AED': 0.272,
    'GEL': 0.370,
    'UAH': 0.0243,
    'CHF': 1.136,
    'CAD': 0.730,
    'AUD': 0.662,
    'INR': 0.0119,
    'THB': 0.0292,
    'PLN': 0.252,
    'CZK': 0.043,
    'ILS': 0.268,
    'AMD': 0.00257,
    'UZS': 0.000079,
    'BTC': 79000.0,
    'ETH': 2500.0,
    'SOL': 104.0,
    'TON': 1.41,
    'USDT': 1.0,
    'BNB': 560.0,
    'XRP': 0.58,
    'DOGE': 0.10
}

CURRENCY_INFO = {
    'USD': {'symbol': '$', 'name_ru': 'Доллар США', 'name_en': 'US Dollar', 'flag': '🇺🇸'},
    'EUR': {'symbol': '€', 'name_ru': 'Евро', 'name_en': 'Euro', 'flag': '🇪🇺'},
    'RUB': {'symbol': '₽', 'name_ru': 'Российский рубль', 'name_en': 'Russian Ruble', 'flag': '🇷🇺'},
    'KZT': {'symbol': '₸', 'name_ru': 'Казахстанский тенге', 'name_en': 'Kazakhstani Tenge', 'flag': '🇰🇿'},
    'BYN': {'symbol': 'Br', 'name_ru': 'Белорусский рубль', 'name_en': 'Belarusian Ruble', 'flag': '🇧🇾'},
    'CNY': {'symbol': '¥', 'name_ru': 'Китайский юань', 'name_en': 'Chinese Yuan', 'flag': '🇨🇳'},
    'GBP': {'symbol': '£', 'name_ru': 'Британский фунт', 'name_en': 'British Pound', 'flag': '🇬🇧'},
    'JPY': {'symbol': '¥', 'name_ru': 'Японская иена', 'name_en': 'Japanese Yen', 'flag': '🇯🇵'},
    'TRY': {'symbol': '₺', 'name_ru': 'Турецкая лира', 'name_en': 'Turkish Lira', 'flag': '🇹🇷'},
    'AED': {'symbol': 'AED', 'name_ru': 'Дирхам ОАЭ', 'name_en': 'UAE Dirham', 'flag': '🇦🇪'},
    'GEL': {'symbol': '₾', 'name_ru': 'Грузинский лари', 'name_en': 'Georgian Lari', 'flag': '🇬🇪'},
    'UAH': {'symbol': '₴', 'name_ru': 'Украинская гривна', 'name_en': 'Ukrainian Hryvnia', 'flag': '🇺🇦'},
    'CHF': {'symbol': 'Fr', 'name_ru': 'Швейцарский франк', 'name_en': 'Swiss Franc', 'flag': '🇨🇭'},
    'CAD': {'symbol': 'C$', 'name_ru': 'Канадский доллар', 'name_en': 'Canadian Dollar', 'flag': '🇨🇦'},
    'AUD': {'symbol': 'A$', 'name_ru': 'Австралийский доллар', 'name_en': 'Australian Dollar', 'flag': '🇦🇺'},
    'INR': {'symbol': '₹', 'name_ru': 'Индийская рупия', 'name_en': 'Indian Rupee', 'flag': '🇮🇳'},
    'THB': {'symbol': '฿', 'name_ru': 'Тайский бат', 'name_en': 'Thai Baht', 'flag': '🇹🇭'},
    'PLN': {'symbol': 'zł', 'name_ru': 'Польский злотый', 'name_en': 'Polish Zloty', 'flag': '🇵🇱'},
    'CZK': {'symbol': 'Kč', 'name_ru': 'Чешская крона', 'name_en': 'Czech Koruna', 'flag': '🇨🇿'},
    'ILS': {'symbol': '₪', 'name_ru': 'Новый израильский шекель', 'name_en': 'Israeli Shekel', 'flag': '🇮🇱'},
    'AMD': {'symbol': '֏', 'name_ru': 'Армянский драм', 'name_en': 'Armenian Dram', 'flag': '🇦🇲'},
    'UZS': {'symbol': 'soʻm', 'name_ru': 'Узбекский сум', 'name_en': 'Uzbek Som', 'flag': '🇺🇿'},
    'BTC': {'symbol': '₿', 'name_ru': 'Биткоин', 'name_en': 'Bitcoin', 'flag': '🪙'},
    'ETH': {'symbol': 'Ξ', 'name_ru': 'Эфириум', 'name_en': 'Ethereum', 'flag': '🪙'},
    'SOL': {'symbol': 'SOL', 'name_ru': 'Солана', 'name_en': 'Solana', 'flag': '🪙'},
    'TON': {'symbol': 'TON', 'name_ru': 'Тонкоин', 'name_en': 'Toncoin', 'flag': '💎'},
    'USDT': {'symbol': '₮', 'name_ru': 'Tether USD', 'name_en': 'Tether USD', 'flag': '💵'},
    'BNB': {'symbol': 'BNB', 'name_ru': 'BNB', 'name_en': 'BNB', 'flag': '🪙'},
    'XRP': {'symbol': 'XRP', 'name_ru': 'Ripple', 'name_en': 'Ripple', 'flag': '🪙'},
    'DOGE': {'symbol': 'DOGE', 'name_ru': 'Dogecoin', 'name_en': 'Dogecoin', 'flag': '🪙'},
}

ALIASES = {
    # USD
    'usd': 'USD', '$': 'USD', 'доллар': 'USD', 'доллара': 'USD', 'долларов': 'USD', 'доллары': 'USD', 'долларах': 'USD',
    'бакс': 'USD', 'бакса': 'USD', 'баксов': 'USD', 'баксы': 'USD', 'грин': 'USD', 'dollar': 'USD', 'dollars': 'USD',
    # EUR
    'eur': 'EUR', '€': 'EUR', 'евро': 'EUR', 'еврик': 'EUR', 'евриков': 'EUR', 'евра': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
    # RUB
    'rub': 'RUB', '₽': 'RUB', 'руб': 'RUB', 'рубль': 'RUB', 'рубля': 'RUB', 'рублей': 'RUB', 'рубли': 'RUB', 'рублях': 'RUB',
    'р': 'RUB', 'деревянный': 'RUB', 'деревянных': 'RUB', 'ruble': 'RUB', 'rubles': 'RUB',
    # KZT
    'kzt': 'KZT', '₸': 'KZT', 'тенге': 'KZT', 'тнг': 'KZT', 'tenge': 'KZT',
    # BYN
    'byn': 'BYN', 'белорусский рубль': 'BYN', 'бел рубль': 'BYN', 'бел рублей': 'BYN', 'бел рубля': 'BYN', 'бел руб': 'BYN', 'зайчик': 'BYN', 'зайчиков': 'BYN', 'белорусских рублей': 'BYN',
    # CNY
    'cny': 'CNY', 'юань': 'CNY', 'юаня': 'CNY', 'юаней': 'CNY', 'юани': 'CNY', 'yuan': 'CNY', 'rmb': 'CNY',
    # GBP
    'gbp': 'GBP', '£': 'GBP', 'фунт': 'GBP', 'фунтов': 'GBP', 'фунта': 'GBP', 'фунты': 'GBP', 'фунт стерлингов': 'GBP', 'фунтов стерлингов': 'GBP', 'британский фунт': 'GBP', 'pound': 'GBP', 'pounds': 'GBP',
    # JPY
    'jpy': 'JPY', 'иена': 'JPY', 'иены': 'JPY', 'иен': 'JPY', 'йена': 'JPY', 'йены': 'JPY', 'йен': 'JPY', 'yen': 'JPY',
    # TRY
    'try': 'TRY', '₺': 'TRY', 'лира': 'TRY', 'лиры': 'TRY', 'лир': 'TRY', 'турецкая лира': 'TRY', 'lira': 'TRY',
    # AED
    'aed': 'AED', 'дирхам': 'AED', 'дирхама': 'AED', 'дирхамов': 'AED', 'дирхамы': 'AED', 'дирхам оаэ': 'AED', 'дихрам': 'AED', 'dirham': 'AED',
    # GEL
    'gel': 'GEL', '₾': 'GEL', 'лари': 'GEL', 'грузинский лари': 'GEL',
    # UAH
    'uah': 'UAH', '₴': 'UAH', 'гривна': 'UAH', 'гривны': 'UAH', 'гривен': 'UAH', 'грн': 'UAH', 'hryvnia': 'UAH',
    # CHF
    'chf': 'CHF', 'швейцарский франк': 'CHF', 'франк': 'CHF', 'франка': 'CHF', 'франков': 'CHF',
    # CAD
    'cad': 'CAD', 'канадский доллар': 'CAD', 'c$': 'CAD',
    # AUD
    'aud': 'AUD', 'австралийский доллар': 'AUD', 'a$': 'AUD',
    # INR
    'inr': 'INR', '₹': 'INR', 'рупия': 'INR', 'рупии': 'INR', 'рупий': 'INR', 'rupee': 'INR',
    # THB
    'thb': 'THB', '฿': 'THB', 'бат': 'THB', 'бата': 'THB', 'батов': 'THB', 'baht': 'THB',
    # PLN
    'pln': 'PLN', 'злотый': 'PLN', 'злотых': 'PLN', 'злотого': 'PLN', 'zloty': 'PLN',
    # CZK
    'czk': 'CZK', 'крона': 'CZK', 'крон': 'CZK', 'чешская крона': 'CZK', 'koruna': 'CZK',
    # ILS
    'ils': 'ILS', 'шекель': 'ILS', 'шекелей': 'ILS', 'shekel': 'ILS',
    # AMD
    'amd': 'AMD', 'драм': 'AMD', 'драмов': 'AMD', 'драма': 'AMD', 'армянский драм': 'AMD',
    # UZS
    'uzs': 'UZS', 'сум': 'UZS', 'сумов': 'UZS', 'сума': 'UZS', 'узбекский сум': 'UZS',
    # BTC
    'btc': 'BTC', '₿': 'BTC', 'биткоин': 'BTC', 'биткоина': 'BTC', 'биткоинов': 'BTC', 'биткоины': 'BTC', 'биток': 'BTC', 'битка': 'BTC', 'битках': 'BTC', 'bitcoin': 'BTC',
    # ETH
    'eth': 'ETH', 'Ξ': 'ETH', 'эфир': 'ETH', 'эфира': 'ETH', 'эфириум': 'ETH', 'эфириума': 'ETH', 'ethereum': 'ETH',
    # SOL
    'sol': 'SOL', 'солана': 'SOL', 'соланы': 'SOL', 'солану': 'SOL', 'solana': 'SOL',
    # TON
    'ton': 'TON', 'тон': 'TON', 'тона': 'TON', 'тонов': 'TON', 'тоны': 'TON', 'тонкоин': 'TON', 'toncoin': 'TON',
    # USDT
    'usdt': 'USDT', '₮': 'USDT', 'тезер': 'USDT', 'тезера': 'USDT', 'tether': 'USDT', 'юсдт': 'USDT',
    # BNB
    'bnb': 'BNB', 'бнб': 'BNB', 'бинанс коин': 'BNB',
    # XRP
    'xrp': 'XRP', 'рипл': 'XRP', 'рипла': 'XRP', 'ripple': 'XRP',
    # DOGE
    'doge': 'DOGE', 'доги': 'DOGE', 'догикоин': 'DOGE', 'доге': 'DOGE', 'dogecoin': 'DOGE'
}


class CurrencyProvider(BaseProvider):
    _rates_cache = FALLBACK_USD_VALUES.copy()
    _rates_timestamp = 0
    _lock = threading.Lock()
    _updating = False

    def __init__(self, history_manager):
        super().__init__(history_manager)
        self._init_rates()

    def _init_rates(self):
        cache_dir = os.path.expanduser("~/.cache/echo_search")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "rates.json")

        # 1. Try loading cached rates
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "rates" in data and isinstance(data["rates"], dict):
                        with self._lock:
                            self._rates_cache.update(data["rates"])
                            self._rates_timestamp = data.get("timestamp", 0)
            except Exception as e:
                print(f"[CurrencyProvider] Error reading cache: {e}")

        # 2. Check if update needed (> 6 hours old or no timestamp)
        now = time.time()
        if now - self._rates_timestamp > 21600:
            threading.Thread(target=self._update_rates_background, daemon=True).start()

    def _update_rates_background(self):
        with self._lock:
            if CurrencyProvider._updating:
                return
            CurrencyProvider._updating = True

        try:
            usd_values = {}
            # 1. Fiat
            try:
                req = urllib.request.Request(
                    "https://open.er-api.com/v6/latest/USD",
                    headers={"User-Agent": "EchoSearch/1.0"}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("result") == "success" and "rates" in data:
                        for code, rate in data["rates"].items():
                            if rate and rate > 0:
                                usd_values[code.upper()] = 1.0 / float(rate)
            except Exception as e:
                print(f"[CurrencyProvider] Fiat update failed: {e}")

            # 2. Crypto
            try:
                crypto_map = {
                    'bitcoin': 'BTC',
                    'ethereum': 'ETH',
                    'solana': 'SOL',
                    'the-open-network': 'TON',
                    'tether': 'USDT',
                    'binancecoin': 'BNB',
                    'ripple': 'XRP',
                    'dogecoin': 'DOGE'
                }
                ids = ",".join(crypto_map.keys())
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
                req = urllib.request.Request(url, headers={"User-Agent": "EchoSearch/1.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    cdata = json.loads(resp.read().decode("utf-8"))
                    for cid, code in crypto_map.items():
                        if cid in cdata and "usd" in cdata[cid]:
                            usd_values[code] = float(cdata[cid]["usd"])
            except Exception as e:
                print(f"[CurrencyProvider] Crypto update failed: {e}")

            if usd_values:
                with self._lock:
                    self._rates_cache.update(usd_values)
                    self._rates_timestamp = int(time.time())

                cache_dir = os.path.expanduser("~/.cache/echo_search")
                cache_file = os.path.join(cache_dir, "rates.json")
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "timestamp": self._rates_timestamp,
                        "base": "USD",
                        "rates": self._rates_cache
                    }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CurrencyProvider] Background update failed: {e}")
        finally:
            with self._lock:
                CurrencyProvider._updating = False

    def _format_value(self, val: float, cur: str, is_ru: bool) -> str:
        if val >= 1000:
            s = f"{val:,.2f}"
        elif val >= 1:
            s = f"{val:,.2f}"
        elif val >= 0.01:
            s = f"{val:,.4f}"
        elif val >= 0.0001:
            s = f"{val:,.6f}"
        else:
            s = f"{val:,.8f}"

        if val < 1:
            s = s.rstrip("0").rstrip(".")

        if is_ru:
            parts = s.split(".")
            whole = parts[0].replace(",", " ")
            dec = parts[1] if len(parts) > 1 else ""
            formatted_num = f"{whole},{dec}" if dec else whole
        else:
            formatted_num = s

        info = CURRENCY_INFO.get(cur, {})
        sym = info.get("symbol", cur)

        if is_ru:
            return f"{formatted_num} {sym}"
        else:
            if cur in ("USD", "GBP"):
                return f"{sym}{formatted_num}"
            elif cur == "EUR":
                return f"€{formatted_num}"
            return f"{formatted_num} {sym}"

    def _create_result(self, val_from: float, cur_from: str, cur_to: str, score: float = 150) -> SearchResult:
        with self._lock:
            rates = self._rates_cache.copy()

        if cur_from not in rates or cur_to not in rates:
            return None

        val_in_usd = val_from * rates[cur_from]
        val_to = val_in_usd / rates[cur_to]

        # Rate calculations (1 unit of cur_from in cur_to, and inverse)
        rate_direct_val = rates[cur_from] / rates[cur_to]
        rate_inverse_val = rates[cur_to] / rates[cur_from]

        is_ru = get_current_language() == "ru"

        info_from = CURRENCY_INFO.get(cur_from, {'symbol': cur_from, 'name_ru': cur_from, 'name_en': cur_from, 'flag': '💵'})
        info_to = CURRENCY_INFO.get(cur_to, {'symbol': cur_to, 'name_ru': cur_to, 'name_en': cur_to, 'flag': '💵'})

        name_from = info_from['name_ru'] if is_ru else info_from['name_en']
        name_to = info_to['name_ru'] if is_ru else info_to['name_en']

        str_val_from = self._format_value(val_from, cur_from, is_ru)
        str_val_to = self._format_value(val_to, cur_to, is_ru)

        str_rate_direct = self._format_value(rate_direct_val, cur_to, is_ru)
        str_rate_inverse = self._format_value(rate_inverse_val, cur_from, is_ru)

        rate_str = f"1 {cur_from} = {str_rate_direct}"
        rate_inv_str = f"1 {cur_to} = {str_rate_inverse}"

        title = f"{str_val_from} = {str_val_to}"
        subtitle = f"{rate_str} • {name_from} → {name_to}"
        copy_text = f"{val_to:.2f}" if val_to >= 1 else f"{val_to:.6f}".rstrip('0')

        preview_data = {
            "val_from": val_from,
            "cur_from": cur_from,
            "cur_from_name": name_from,
            "cur_from_flag": info_from.get('flag', ''),
            "val_to": val_to,
            "cur_to": cur_to,
            "cur_to_name": name_to,
            "cur_to_flag": info_to.get('flag', ''),
            "str_val_from": str_val_from,
            "str_val_to": str_val_to,
            "rate_str": rate_str,
            "rate_inv_str": rate_inv_str,
            "copy_text": copy_text,
            "full_copy_text": f"{title} ({rate_str})"
        }

        def _copy_val():
            try:
                display = Gdk.Display.get_default()
                if display:
                    display.get_clipboard().set(copy_text)
            except Exception:
                pass

        def _copy_all():
            try:
                display = Gdk.Display.get_default()
                if display:
                    display.get_clipboard().set(f"{title} ({rate_str})")
            except Exception:
                pass

        return SearchResult(
            id=f"cur_{cur_from}_{cur_to}_{val_from}",
            title=title,
            subtitle=subtitle,
            icon=CURRENCY_ICON_PATH if os.path.exists(CURRENCY_ICON_PATH) else "format-currency",
            score=score,
            category="Currency",
            provider="CurrencyProvider",
            preview_data=preview_data,
            action_execute=_copy_val,
            action_copy=_copy_val
        )

    def search(self, query: str, limit: int = 5, category_filter: str = None) -> list[SearchResult]:
        if category_filter not in (None, "All", "Units", "Math", "Currency"):
            return []

        if not query:
            return []

        q = query.strip().lower()
        if len(q) < 2:
            return []

        is_ru = get_current_language() == "ru"
        has_cyrillic = bool(re.search(r'[а-яё]', q))
        is_ru_context = is_ru or has_cyrillic
        default_target = "RUB" if is_ru_context else "USD"

        # Normalize symbols attached to numbers
        # 100$ -> 100 $
        q = re.sub(r"([0-9\.,]+)\s*([\$\€\₽\₸\£\₺\₾\₴\₹\฿\₿\Ξ\₮])", r"\1 \2", q)
        q = re.sub(r"([\$\€\₽\₸\£\₺\₾\₴\₹\฿\₿\Ξ\₮])\s*([0-9\.,]+)", r"\2 \1", q)

        results = []

        # Case 1: 'курс <cur>' or 'rate of <cur>'
        rate_match = re.match(r'^(?:курс|rate\s+of|rate|цена|стоимость)\s+([a-zа-яё\$\€\₽\₸\£\₺\₾\₴\₹\฿\₿\Ξ\₮]+)$', q)
        if rate_match:
            raw_cur = rate_match.group(1)
            cur = ALIASES.get(raw_cur)
            if cur:
                if cur != default_target:
                    target = default_target
                else:
                    target = "USD" if default_target == "RUB" else "EUR"
                res = self._create_result(1.0, cur, target, score=160)
                if res:
                    results.append(res)
                if target == "RUB" and cur not in ("USD", "EUR"):
                    res2 = self._create_result(1.0, cur, "USD", score=155)
                    if res2:
                        results.append(res2)
                return results

        # Case 2: '<val> <cur_from> (in/to/в/во/->) <cur_to>' or '<val> <cur_from> <cur_to>'
        conv_match = re.match(r'^([\d\s\.,]+)\s*([a-zа-яё\$\€\₽\₸\£\₺\₾\₴\₹\฿\₿\Ξ\₮]+)(?:\s*(?:in|to|в|во|->)\s*|\s+)([a-zа-яё\$\€\₽\₸\£\₺\₾\₴\₹\฿\₿\Ξ\₮]+)$', q)
        if conv_match:
            val_str, raw_from, raw_to = conv_match.groups()
            cur_from = ALIASES.get(raw_from)
            cur_to = ALIASES.get(raw_to)
            if cur_from and cur_to and cur_from != cur_to:
                try:
                    val = float(val_str.replace(' ', '').replace(',', '.'))
                    res = self._create_result(val, cur_from, cur_to, score=160)
                    if res:
                        return [res]
                except ValueError:
                    pass

        # Case 3: '<cur_from> (in/to/в/во/->) <cur_to>' (implied amount 1)
        pair_match = re.match(r'^([a-zа-яё\$\€\₽\₸\£\₺\₾\₴\₹\฿\₿\Ξ\₮]+)\s*(?:in|to|в|во|->)\s*([a-zа-яё\$\€\₽\₸\£\₺\₾\₴\₹\฿\₿\Ξ\₮]+)$', q)
        if pair_match:
            cur_from = ALIASES.get(pair_match.group(1))
            cur_to = ALIASES.get(pair_match.group(2))
            if cur_from and cur_to and cur_from != cur_to:
                res = self._create_result(1.0, cur_from, cur_to, score=155)
                if res:
                    return [res]

        # Case 4: '<val> <cur_from>' (single currency query)
        single_match = re.match(r'^([\d\s\.,]+)\s*([a-zа-яё\$\€\₽\₸\£\₺\₾\₴\₹\฿\₿\Ξ\₮]+)$', q)
        if single_match:
            val_str, raw_from = single_match.groups()
            # Avoid single letter 'р' or 'т' triggering on ambiguous inputs
            if raw_from in ('р', 'т', 'д', 'к', 'м'):
                return []
            cur_from = ALIASES.get(raw_from)
            if cur_from:
                try:
                    val = float(val_str.replace(' ', '').replace(',', '.'))
                    targets = []
                    if is_ru_context:
                        if cur_from == "RUB":
                            targets = ["USD", "EUR"]
                        elif cur_from in ("BTC", "ETH", "SOL", "TON"):
                            targets = ["USD", "RUB"]
                        elif cur_from == "USD":
                            targets = ["RUB", "EUR"]
                        else:
                            targets = ["RUB", "USD"]
                    else:
                        if cur_from == "USD":
                            targets = ["EUR", "GBP"]
                        elif cur_from == "EUR":
                            targets = ["USD", "GBP"]
                        elif cur_from in ("BTC", "ETH", "SOL", "TON"):
                            targets = ["USD", "EUR"]
                        else:
                            targets = ["USD", "EUR"]

                    for idx, target in enumerate(targets):
                        res = self._create_result(val, cur_from, target, score=150 - idx * 5)
                        if res:
                            results.append(res)
                    return results
                except ValueError:
                    pass

        return []
