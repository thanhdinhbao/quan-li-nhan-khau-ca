import re
import unicodedata
from datetime import datetime

def vietnamese_unaccent(text: str) -> str:
    """
    Removes Vietnamese accents and converts string to lowercase for unaccented search.
    Example: "Đinh Bảo Thành" -> "dinh bao thanh"
    """
    if not text:
        return ""
    
    text = text.replace("Đ", "D").replace("đ", "d")
    # Normalize unicode to NFD decomposition and filter out combining marks
    nfkd_form = unicodedata.normalize('NFD', text)
    unaccented = "".join([c for c in nfkd_form if unicodedata.category(c) != 'Mn'])
    return unaccented.lower().strip()

def format_date_vn(date_obj) -> str:
    """Formats date object or string yyyy-mm-dd to dd/mm/yyyy"""
    if not date_obj:
        return ""
    if isinstance(date_obj, str):
        try:
            # Check string format
            if "-" in date_obj:
                dt = datetime.strptime(date_obj.split("T")[0], "%Y-%m-%d")
                return dt.strftime("%d/%m/%Y")
            elif "/" in date_obj:
                parts = date_obj.split("/")
                if len(parts) == 3 and len(parts[2]) == 4:
                    return date_obj
        except Exception:
            return date_obj
    elif hasattr(date_obj, "strftime"):
        return date_obj.strftime("%d/%m/%Y")
    return str(date_obj)

def parse_date_to_iso(date_str: str) -> str:
    """
    Parses various date strings (dd/mm/yyyy, yyyy-mm-dd, etc.) to ISO format yyyy-mm-dd.
    Returns empty string if invalid or empty.
    """
    if not date_str:
        return ""
    date_str = str(date_str).strip()
    if not date_str:
        return ""
    
    # Try common formats
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str

def mask_id_card(id_card: str, has_full_permission: bool = True) -> str:
    """
    Masks middle digits of CCCD for privacy if permission is False.
    Example: 036201012345 -> 0362******45
    """
    if not id_card:
        return ""
    if has_full_permission:
        return id_card
    id_str = str(id_card).strip()
    if len(id_str) >= 9:
        return id_str[:4] + "*" * (len(id_str) - 6) + id_str[-2:]
    elif len(id_str) > 4:
        return id_str[:2] + "*" * (len(id_str) - 4) + id_str[-2:]
    return id_str

def mask_phone(phone: str, has_full_permission: bool = True) -> str:
    """
    Masks middle digits of phone number if permission is False.
    Example: 0912345678 -> 0912***678
    """
    if not phone:
        return ""
    if has_full_permission:
        return phone
    phone_str = str(phone).strip()
    if len(phone_str) >= 7:
        return phone_str[:4] + "***" + phone_str[-3:]
    return phone_str

def format_number(num: int) -> str:
    """Formats integer with dot thousands separator (e.g. 1.248)"""
    try:
        return f"{int(num):,}".replace(",", ".")
    except Exception:
        return str(num)
