"""
Интеграция с Nominatim (OpenStreetMap) для геокодирования.
- reverse: координаты → адрес
- search: запрос по имени/адресу → результаты

https://nominatim.org/release-docs/latest/api/Overview/
Политика: 1 запрос/сек, User-Agent + Referer по https://operations.osmfoundation.org/policies/nominatim/
"""

import urllib.request
import urllib.parse
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
# Политика Nominatim: User-Agent + Referer обязательны
USER_AGENT = "ESM-ConsciousCitizen/1.0 (https://github.com; contact@esm.local)"
REFERER = "http://localhost:8000/"


def _get_config() -> tuple[str, dict]:
    """URL и заголовки (с переопределением через settings)."""
    try:
        from django.conf import settings as s
        base = getattr(s, 'NOMINATIM_BASE_URL', NOMINATIM_BASE)
        headers = {
            "User-Agent": getattr(s, 'NOMINATIM_USER_AGENT', USER_AGENT),
            "Referer": getattr(s, 'NOMINATIM_REFERER', REFERER),
            "Accept-Language": "ru",
        }
    except Exception:
        base = NOMINATIM_BASE
        headers = {"User-Agent": USER_AGENT, "Referer": REFERER, "Accept-Language": "ru"}
    return base, headers


def _request(path: str, params: dict) -> tuple[Optional[dict], Optional[str]]:
    """
    Выполняет GET-запрос к Nominatim API.
    Returns: (data, error_message)
    """
    base, headers = _get_config()
    url = f"{base}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode()
            result = json.loads(data) if data else None
            if isinstance(result, dict) and "error" in result:
                return None, result.get("error", "Nominatim error")
            return result, None
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        err = f"HTTP {e.code}: {body[:200]}"
        logger.warning("Nominatim HTTP error: %s", err)
        return None, err
    except urllib.error.URLError as e:
        err = str(e.reason) if e.reason else str(e)
        logger.warning("Nominatim URL error: %s", err)
        return None, f"Сеть недоступна: {err}"
    except json.JSONDecodeError as e:
        logger.warning("Nominatim JSON error: %s", e)
        return None, "Неверный ответ сервера"
    except Exception as e:
        logger.exception("Nominatim request failed")
        return None, str(e)


def reverse_geocode(lat: float, lon: float, zoom: int = 18) -> tuple[Optional[dict], Optional[str]]:
    """
    Обратное геокодирование: координаты → адрес.
    
    Returns:
        (data, None) при успехе или (None, error_message) при ошибке
    """
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "addressdetails": 1,
    }
    result, err = _request("/reverse", params)
    if err:
        return None, err
    if isinstance(result, dict) and "error" not in result:
        return result, None
    if isinstance(result, list) and result:
        return result[0], None
    return None, "Пустой ответ от Nominatim"


def search(query: str, limit: int = 5) -> list:
    """
    Поиск по имени или адресу.
    
    Args:
        query: строка поиска (название, адрес, тип объекта)
        limit: макс. число результатов
    
    Returns:
        Список dict с display_name, lat, lon, address и др.
    """
    params = {
        "format": "json",
        "q": query,
        "limit": limit,
        "addressdetails": 1,
    }
    result, err = _request("/search", params)
    if err or not isinstance(result, list):
        return []
    return result


def build_address_from_osm(address_parts: dict) -> str:
    """
    Собирает строку адреса из address_parts ответа Nominatim.
    Маппинг по ТЗ: city, road, house_number → display_name
    """
    if not address_parts:
        return ""
    parts = []
    for key in ["house_number", "road", "city", "state", "country"]:
        val = address_parts.get(key)
        if val:
            parts.append(str(val))
    return ", ".join(parts) if parts else address_parts.get("display_name", "")


def parse_reverse_response(data: dict) -> dict:
    """
    Парсит ответ reverse в удобный формат по маппингу ТЗ 10.3.
    
    Returns:
        {
            "latitude": float,
            "longitude": float,
            "address": str,
            "city": str | None,
            "street": str | None,   # road
            "house": str | None,    # house_number
            "state": str | None,    # область/регион
        }
    """
    if not data:
        return {}
    addr = data.get("address", {}) or {}
    return {
        "latitude": float(data.get("lat", 0)),
        "longitude": float(data.get("lon", 0)),
        "address": build_address_from_osm(addr) or data.get("display_name", ""),
        "city": addr.get("city") or addr.get("town") or addr.get("village"),
        "street": addr.get("road"),
        "house": addr.get("house_number"),
        "state": addr.get("state") or addr.get("region"),
    }
