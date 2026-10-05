from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, date
from utils.formatters import format_date_vn, mask_id_card, mask_phone

@dataclass
class Area:
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    description: Optional[str] = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    person_count: int = 0
    household_count: int = 0

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        keys = row.keys() if hasattr(row, 'keys') else []
        return cls(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"] if "created_at" in keys else None,
            updated_at=row["updated_at"] if "updated_at" in keys else None,
            person_count=row["person_count"] if "person_count" in keys else 0,
            household_count=row["household_count"] if "household_count" in keys else 0
        )

@dataclass
class Person:
    id: Optional[int] = None
    person_code: str = ""
    full_name: str = ""
    normalized_name: str = ""
    dob: Optional[str] = ""
    gender: str = "Nam"
    id_card_number: Optional[str] = ""
    id_card_date: Optional[str] = ""
    id_card_place: Optional[str] = ""
    hometown: Optional[str] = ""
    ethnicity: str = "Kinh"
    nationality: str = "Việt Nam"
    religion: str = "Không"
    occupation: Optional[str] = ""
    workplace: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    marital_status: Optional[str] = "Độc thân"
    permanent_address: Optional[str] = ""
    temporary_address: Optional[str] = ""
    current_address: Optional[str] = ""
    area_id: int = 1
    area_name: Optional[str] = ""
    house_number: Optional[str] = ""
    street_village: Optional[str] = ""
    permanent_reg_date: Optional[str] = ""
    temporary_reg_date: Optional[str] = ""
    residence_status: str = "Thường trú"
    father_name: Optional[str] = ""
    father_id_card: Optional[str] = ""
    mother_name: Optional[str] = ""
    mother_id_card: Optional[str] = ""
    spouse_name: Optional[str] = ""
    spouse_id_card: Optional[str] = ""
    relationship_with_head: Optional[str] = ""
    household_id: Optional[int] = None
    household_code: Optional[str] = ""
    avatar_path: Optional[str] = ""
    notes: Optional[str] = ""
    is_deleted: int = 0
    deleted_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        keys = row.keys() if hasattr(row, 'keys') else []
        return cls(
            id=row["id"],
            person_code=row["person_code"],
            full_name=row["full_name"],
            normalized_name=row["normalized_name"] if "normalized_name" in keys else "",
            dob=row["dob"] if "dob" in keys else "",
            gender=row["gender"] if "gender" in keys else "Nam",
            id_card_number=row["id_card_number"] if "id_card_number" in keys else "",
            id_card_date=row["id_card_date"] if "id_card_date" in keys else "",
            id_card_place=row["id_card_place"] if "id_card_place" in keys else "",
            hometown=row["hometown"] if "hometown" in keys else "",
            ethnicity=row["ethnicity"] if "ethnicity" in keys else "Kinh",
            nationality=row["nationality"] if "nationality" in keys else "Việt Nam",
            religion=row["religion"] if "religion" in keys else "Không",
            occupation=row["occupation"] if "occupation" in keys else "",
            workplace=row["workplace"] if "workplace" in keys else "",
            phone=row["phone"] if "phone" in keys else "",
            email=row["email"] if "email" in keys else "",
            marital_status=row["marital_status"] if "marital_status" in keys else "",
            permanent_address=row["permanent_address"] if "permanent_address" in keys else "",
            temporary_address=row["temporary_address"] if "temporary_address" in keys else "",
            current_address=row["current_address"] if "current_address" in keys else "",
            area_id=row["area_id"] if "area_id" in keys else 1,
            area_name=row["area_name"] if "area_name" in keys else "",
            house_number=row["house_number"] if "house_number" in keys else "",
            street_village=row["street_village"] if "street_village" in keys else "",
            permanent_reg_date=row["permanent_reg_date"] if "permanent_reg_date" in keys else "",
            temporary_reg_date=row["temporary_reg_date"] if "temporary_reg_date" in keys else "",
            residence_status=row["residence_status"] if "residence_status" in keys else "Thường trú",
            father_name=row["father_name"] if "father_name" in keys else "",
            father_id_card=row["father_id_card"] if "father_id_card" in keys else "",
            mother_name=row["mother_name"] if "mother_name" in keys else "",
            mother_id_card=row["mother_id_card"] if "mother_id_card" in keys else "",
            spouse_name=row["spouse_name"] if "spouse_name" in keys else "",
            spouse_id_card=row["spouse_id_card"] if "spouse_id_card" in keys else "",
            relationship_with_head=row["relationship_with_head"] if "relationship_with_head" in keys else "",
            household_id=row["household_id"] if "household_id" in keys else None,
            household_code=row["household_code"] if "household_code" in keys else "",
            avatar_path=row["avatar_path"] if "avatar_path" in keys else "",
            notes=row["notes"] if "notes" in keys else "",
            is_deleted=row["is_deleted"] if "is_deleted" in keys else 0,
            deleted_at=row["deleted_at"] if "deleted_at" in keys else None,
            created_at=row["created_at"] if "created_at" in keys else None,
            updated_at=row["updated_at"] if "updated_at" in keys else None
        )

@dataclass
class Household:
    id: Optional[int] = None
    household_code: str = ""
    household_number: Optional[str] = ""
    area_id: int = 1
    area_name: Optional[str] = ""
    head_person_id: Optional[int] = None
    head_full_name: Optional[str] = ""
    address_street: Optional[str] = ""
    full_address: Optional[str] = ""
    created_date: Optional[str] = ""
    status: str = "ACTIVE"
    notes: Optional[str] = ""
    member_count: int = 0
    members: List[Person] = field(default_factory=list)

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        keys = row.keys() if hasattr(row, 'keys') else []
        return cls(
            id=row["id"],
            household_code=row["household_code"],
            household_number=row["household_number"] if "household_number" in keys else "",
            area_id=row["area_id"] if "area_id" in keys else 1,
            area_name=row["area_name"] if "area_name" in keys else "",
            head_person_id=row["head_person_id"] if "head_person_id" in keys else None,
            head_full_name=row["head_full_name"] if "head_full_name" in keys else "",
            address_street=row["address_street"] if "address_street" in keys else "",
            full_address=row["full_address"] if "full_address" in keys else "",
            created_date=row["created_date"] if "created_date" in keys else "",
            status=row["status"] if "status" in keys else "ACTIVE",
            notes=row["notes"] if "notes" in keys else "",
            member_count=row["member_count"] if "member_count" in keys else 0
        )

@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    full_name: str = ""
    role_id: int = 2
    role_code: str = ""
    role_name: str = ""
    position: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    is_active: int = 1
    permissions: List[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row, permissions=None):
        if not row:
            return None
        keys = row.keys() if hasattr(row, 'keys') else []
        return cls(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            role_id=row["role_id"],
            role_code=row["role_code"] if "role_code" in keys else "",
            role_name=row["role_name"] if "role_name" in keys else "",
            position=row["position"] if "position" in keys else "",
            email=row["email"] if "email" in keys else "",
            phone=row["phone"] if "phone" in keys else "",
            is_active=row["is_active"] if "is_active" in keys else 1,
            permissions=permissions or []
        )

    def has_permission(self, perm_code: str) -> bool:
        """Check if user holds specific permission."""
        if self.role_code == "ADMIN":
            return True
        return perm_code in self.permissions

@dataclass
class AuditLog:
    id: Optional[int] = None
    user_id: Optional[int] = None
    username: str = ""
    action: str = ""
    target_type: Optional[str] = ""
    target_id: Optional[int] = None
    details: str = ""
    ip_address: str = "127.0.0.1"
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            username=row["username"],
            action=row["action"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            details=row["details"],
            ip_address=row["ip_address"],
            created_at=row["created_at"]
        )
