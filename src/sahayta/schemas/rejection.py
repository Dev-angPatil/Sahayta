"""
src/sahayta/schemas/rejection.py
Deterministic Rejection Models and Codes for Invalid, Fictional, or Fraudulent Entities.
"""

from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class RejectionCode(str, Enum):
    FAKE_GOVERNMENT_BODY = "FAKE_GOVERNMENT_BODY"
    FRAUDULENT_OR_FICTITIOUS_SCHEME = "FRAUDULENT_OR_FICTITIOUS_SCHEME"
    OUT_OF_SCOPE_COMMERCIAL_DISPUTE = "OUT_OF_SCOPE_COMMERCIAL_DISPUTE"
    UNVERIFIED_CIVIC_ENTITY = "UNVERIFIED_CIVIC_ENTITY"


class TriageRejectionResponse(BaseModel):
    """
    Structured response returned when an incoming citizen complaint is rejected
    by Gate 0 guardrails or unverified civic entity filters.
    
    Supports both 'rejected_entity' / 'flagged_entity', 'reason' / 'rejection_reason',
    and 'suggested_action' / 'official_advice' for 100% interoperability.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        validate_assignment=True,
    )

    status: str = Field(default="REJECTED", description="Status string: 'REJECTED' or 'rejected'")
    rejection_code: RejectionCode = Field(..., description="Canonical rejection classification code")
    is_valid_civic_grievance: bool = Field(default=False, description="Strictly False for all rejections")
    rejected_entity: str = Field(..., alias="flagged_entity", description="Name of the rejected entity or scheme")
    message: str = Field(..., description="Citizen-facing clear rejection notice")
    reason: str = Field(..., alias="rejection_reason", description="Formal administrative justification")
    suggested_action: str = Field(..., alias="official_advice", description="Advisory on legitimate grievance avenues")

    @field_validator("is_valid_civic_grievance")
    @classmethod
    def validate_civic_grievance_false(cls, v: bool) -> bool:
        if v is not False:
            raise ValueError("is_valid_civic_grievance must strictly be False for any rejection")
        return False

    @field_validator("status")
    @classmethod
    def validate_status_value(cls, v: str) -> str:
        if v.upper() != "REJECTED":
            raise ValueError("status must be 'REJECTED' or 'rejected'")
        return v.upper()

    @property
    def flagged_entity(self) -> str:
        return self.rejected_entity

    @property
    def rejection_reason(self) -> str:
        return self.reason

    @property
    def official_advice(self) -> str:
        return self.suggested_action

    def __getitem__(self, item: str) -> Any:
        if item in ("flagged_entity", "rejected_entity"):
            return self.rejected_entity
        if item in ("rejection_reason", "reason"):
            return self.reason
        if item in ("official_advice", "suggested_action"):
            return self.suggested_action
        if hasattr(self, item):
            val = getattr(self, item)
            if isinstance(val, Enum):
                return val.value
            return val
        raise KeyError(item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rejection_code": self.rejection_code.value,
            "is_valid_civic_grievance": self.is_valid_civic_grievance,
            "rejected_entity": self.rejected_entity,
            "flagged_entity": self.rejected_entity,
            "message": self.message,
            "reason": self.reason,
            "rejection_reason": self.reason,
            "suggested_action": self.suggested_action,
            "official_advice": self.suggested_action,
        }
