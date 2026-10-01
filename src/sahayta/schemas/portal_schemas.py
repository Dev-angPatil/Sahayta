"""
src/sahayta/schemas/portal_schemas.py
Canonical Grounded Portal Schemas with Strict Pydantic v2 Validation (extra='forbid').
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import re

# =====================================================================
# COMMON VALIDATION REGEX PATTERNS
# =====================================================================

INDIAN_MOBILE_REGEX = r"^[6-9]\d{9}$"
INDIAN_PINCODE_REGEX = r"^[1-9][0-9]{5}$"
RATION_CARD_REGEX = r"^[A-Za-z0-9]{8,16}$"
ACCOUNT_NO_REGEX = r"^[A-Za-z0-9\-\/]{5,20}$"
METER_NO_REGEX = r"^[A-Za-z0-9\-\_]{3,30}$"

# =====================================================================
# PORTAL & GRIEVANCE TAXONOMY ENUMS
# =====================================================================

class PortalType(str, Enum):
    CPGRAMS = "CPGRAMS"
    STATE_PDS = "STATE_PDS"
    DISCOM_POWER = "DISCOM_POWER"
    WATER_BOARD = "WATER_BOARD"


class PDSGrievanceCategory(str, Enum):
    RATION_NON_DISBURSAL = "ration_non_disbursal"
    BIOMETRIC_FAILURE = "biometric_authentication_failure"
    FPS_MALPRACTICE = "fps_overcharging_malpractice"
    AADHAAR_SEEDING = "aadhaar_seeding_issue"
    NEW_CARD_DELAY = "new_card_or_modification_delay"
    POOR_QUALITY = "poor_foodgrain_quality"
    ONORC_PORTABILITY = "onorc_portability_denial"


class DiscomIssueCategory(str, Enum):
    BILLING_ERROR = "billing_error"
    PROLONGED_OUTAGE = "prolonged_outage"
    VOLTAGE_FLUCTUATION = "voltage_fluctuation"
    METER_FAULT = "meter_fault"
    NEW_CONNECTION_DELAY = "new_connection_delay"
    HAZARDOUS_INFRASTRUCTURE = "hazardous_infrastructure"


class WaterIssueCategory(str, Enum):
    CONTAMINATED_WATER = "contaminated_water"
    NO_WATER_SUPPLY = "no_water_supply"
    PIPE_BURST_LEAKAGE = "pipe_burst_or_leakage"
    SEWER_OVERFLOW = "sewer_overflow"
    FAULTY_WATER_METER = "faulty_water_meter"
    ILLEGAL_TAPPING = "illegal_tapping_or_booster"
    WATER_BILLING_DISPUTE = "water_billing_dispute"


# =====================================================================
# 1. CPGRAMS SCHEMA MODEL
# =====================================================================

class CpgramsGrievancePayload(BaseModel):
    """
    Centralized Public Grievance Redress and Monitoring System (CPGRAMS) payload.
    Target Jurisdiction: Union Government of India Ministries & Departments.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )

    schema_id: str = Field(default="GOVTECH_CPGRAMS_V1", description="Authoritative schema identifier")
    portal: str = Field(default="CPGRAMS", description="Portal type")
    
    # Required Fields
    complainant_name: str = Field(..., min_length=2, max_length=100, description="Full legal name of complainant")
    mobile_number: str = Field(..., pattern=INDIAN_MOBILE_REGEX, description="10-digit Indian mobile number")
    email: EmailStr = Field(..., description="Valid email address for official communications")
    address: str = Field(..., min_length=5, max_length=250, description="Complete postal address")
    state: str = Field(..., min_length=2, max_length=50, description="Indian State or Union Territory")
    district: str = Field(..., min_length=2, max_length=60, description="Administrative District")
    pincode: str = Field(..., pattern=INDIAN_PINCODE_REGEX, description="6-digit Indian PIN code")
    ministry_department: str = Field(..., min_length=2, max_length=120, description="Target Central Ministry or Department")
    grievance_category: str = Field(..., min_length=3, max_length=120, description="Specific grievance category head")
    grievance_description: str = Field(..., min_length=10, max_length=4000, alias="description", description="Chronological facts of grievance")

    # Optional Fields
    reference_number: Optional[str] = Field(None, max_length=50, description="Prior reference ID (PNR, UTR, etc.)")
    previous_grievance_id: Optional[str] = Field(None, max_length=50, description="Prior CPGRAMS registration number")

    @property
    def description(self) -> str:
        return self.grievance_description


# =====================================================================
# 2. STATE PDS SCHEMA MODEL
# =====================================================================

class StatePdsGrievancePayload(BaseModel):
    """
    State Public Distribution System (PDS / Ration) grievance payload.
    Target Jurisdiction: State Food, Civil Supplies & Consumer Affairs Directorate.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )

    schema_id: str = Field(default="GOVTECH_STATE_PDS_V1", description="Authoritative schema identifier")
    portal: str = Field(default="STATE_PDS", description="Portal type")

    # Required Fields
    complainant_name: str = Field(..., min_length=2, max_length=100, description="Ration card holder or beneficiary name")
    ration_card_number: str = Field(..., pattern=RATION_CARD_REGEX, description="8-16 digit Ration Card Number (NFSA/SRC)")
    state: str = Field(..., min_length=2, max_length=50, description="State where ration card is registered")
    district: str = Field(..., min_length=2, max_length=60, description="Administrative District")
    fps_shop_id_or_name: str = Field(..., min_length=2, max_length=100, description="Fair Price Shop number or dealer name")
    grievance_category: str = Field(..., min_length=3, max_length=100, description="Categorical PDS issue type")
    grievance_description: str = Field(..., min_length=10, max_length=3000, alias="description", description="Specific statement of grievance")

    # Optional Fields
    mobile_number: Optional[str] = Field(None, pattern=INDIAN_MOBILE_REGEX, description="Contact mobile number")
    fair_price_shop_location: Optional[str] = Field(None, min_length=2, max_length=150, description="FPS shop village/locality")
    card_type: Optional[str] = Field(None, max_length=30, description="Ration card type: AAY, PHH, BPL, etc.")

    @property
    def description(self) -> str:
        return self.grievance_description


# =====================================================================
# 3. PUBLIC UTILITIES: DISCOM POWER SCHEMA MODEL
# =====================================================================

class DiscomGrievancePayload(BaseModel):
    """
    Public Utility - Electricity Distribution Company (DISCOM) grievance payload.
    Target Jurisdiction: State Electricity Regulatory Commission / CGRF.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )

    schema_id: str = Field(default="GOVTECH_UTILITY_DISCOM_V1", description="Authoritative schema identifier")
    portal: str = Field(default="DISCOM_POWER", description="Portal type")

    # Required Fields
    consumer_account_number: str = Field(..., pattern=ACCOUNT_NO_REGEX, description="Consumer CA No, K-No, or Account ID")
    utility_provider: str = Field(..., min_length=2, max_length=100, description="Verified DISCOM provider name")
    meter_number: str = Field(..., pattern=METER_NO_REGEX, description="Electric meter serial number stamped on unit")
    district_subdivision: str = Field(..., min_length=2, max_length=80, description="Sub-division office or distribution area")
    issue_category: str = Field(..., description="Power grievance category")
    grievance_description: str = Field(..., min_length=10, max_length=3000, alias="description", description="Details of fault")

    # Optional Fields
    complainant_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Registered consumer or applicant name")
    mobile_number: Optional[str] = Field(None, pattern=INDIAN_MOBILE_REGEX, description="Contact mobile number")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    address: Optional[str] = Field(None, min_length=3, max_length=250, description="Premises address")
    billing_month: Optional[str] = Field(None, max_length=30, description="Disputed billing month/cycle")

    @property
    def description(self) -> str:
        return self.grievance_description


# =====================================================================
# 4. PUBLIC UTILITIES: MUNICIPAL WATER BOARD SCHEMA MODEL
# =====================================================================

class WaterBoardGrievancePayload(BaseModel):
    """
    Public Utility - Municipal Water Supply & Sewerage Board grievance payload.
    Target Jurisdiction: Urban Local Body / Jal Board / Water Authority.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )

    schema_id: str = Field(default="GOVTECH_UTILITY_WATER_V1", description="Authoritative schema identifier")
    portal: str = Field(default="WATER_BOARD", description="Portal type")

    # Required Fields
    consumer_number: str = Field(..., pattern=ACCOUNT_NO_REGEX, description="Water Connection Number, CAN, or RR No")
    water_board_name: str = Field(..., min_length=2, max_length=100, description="Official Water Board Name")
    area_locality: str = Field(..., min_length=2, max_length=120, description="Ward, Colony, Sector, or Mohalla")
    issue_category: str = Field(..., description="Water or sewerage issue category")
    grievance_description: str = Field(..., min_length=10, max_length=3000, alias="description", description="Disruption facts")

    # Optional Fields
    complainant_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Resident or consumer name")
    mobile_number: Optional[str] = Field(None, pattern=INDIAN_MOBILE_REGEX, description="Contact mobile number")
    address: Optional[str] = Field(None, min_length=3, max_length=250, description="Complete street address")
    landmark: Optional[str] = Field(None, min_length=2, max_length=100, description="Prominent landmark nearby")
    ward_number: Optional[str] = Field(None, max_length=30, description="Municipal ward number")

    @property
    def description(self) -> str:
        return self.grievance_description
