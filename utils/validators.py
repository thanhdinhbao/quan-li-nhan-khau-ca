import re
from datetime import datetime

def validate_full_name(name: str) -> tuple[bool, str]:
    """Validates person full name."""
    if not name or not name.strip():
        return False, "Họ và tên không được để trống."
    cleaned = name.strip()
    if len(cleaned) < 2:
        return False, "Họ và tên quá ngắn (ít nhất 2 ký tự)."
    if len(cleaned) > 100:
        return False, "Họ và tên vượt quá 100 ký tự."
    return True, ""

def validate_id_card(id_card: str, allow_empty: bool = True) -> tuple[bool, str]:
    """
    Validates Vietnam Citizen ID (CCCD/CMND).
    CMND: 9 or 12 digits
    CCCD: 12 digits
    """
    if not id_card or not id_card.strip():
        if allow_empty:
            return True, ""
        return False, "Số CCCD/CMND không được để trống."
    
    cleaned = id_card.strip()
    if not cleaned.isdigit():
        return False, "Số CCCD/CMND chỉ được chứa các chữ số."
    if len(cleaned) not in [9, 12]:
        return False, "Số CCCD/CMND phải có độ dài 9 số (CMND cũ) hoặc 12 số (CCCD mới)."
    return True, ""

def validate_phone(phone: str, allow_empty: bool = True) -> tuple[bool, str]:
    """Validates Vietnam phone number format."""
    if not phone or not phone.strip():
        if allow_empty:
            return True, ""
        return False, "Số điện thoại không được để trống."
    
    cleaned = phone.strip()
    # Accept standard formats e.g. 0912345678, +84912345678, 0243123456
    pattern = r"^(0|\+84)[3|5|7|8|9|2][0-9]{8,9}$"
    if not re.match(pattern, cleaned):
        return False, "Số điện thoại không đúng định dạng (Ví dụ: 0912345678 hoặc 0243888999)."
    return True, ""

def validate_dob(dob_str: str) -> tuple[bool, str]:
    """Validates date of birth string (yyyy-mm-dd or dd/mm/yyyy). Must not be in the future."""
    if not dob_str or not dob_str.strip():
        return False, "Ngày sinh không được để trống."
    
    try:
        if "-" in dob_str:
            dt = datetime.strptime(dob_str.strip(), "%Y-%m-%d")
        elif "/" in dob_str:
            dt = datetime.strptime(dob_str.strip(), "%d/%m/%Y")
        else:
            return False, "Định dạng ngày sinh không hợp lệ (dd/mm/yyyy hoặc yyyy-mm-dd)."
        
        if dt > datetime.now():
            return False, "Ngày sinh không được lớn hơn ngày hiện tại."
        if dt.year < 1900:
            return False, "Năm sinh phải lớn hơn 1900."
        return True, ""
    except ValueError:
        return False, "Ngày sinh không hợp lệ."

def validate_area_id(area_id: int) -> tuple[bool, str]:
    """Validates that area selection is selected."""
    if not area_id or area_id <= 0:
        return False, "Vui lòng chọn Khu vực/Thôn/Tổ dân phố."
    return True, ""
