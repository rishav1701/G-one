from datetime import datetime
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator


class ObservationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    admission_id: str = Field(min_length=36, max_length=36)
    measured_at: datetime
    respiration_rate: StrictInt | None = Field(default=None)
    spo2: StrictInt | None = Field(default=None)
    supplemental_o2: StrictBool | None = Field(default=None)
    systolic_bp: StrictInt | None = Field(default=None)
    pulse: StrictInt | None = Field(default=None)
    consciousness: str | None = Field(default=None, max_length=20)
    temperature: Decimal | None = Field(default=None, max_digits=3, decimal_places=1)
    source: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    source_record_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    is_simulated: bool = False

    @field_validator("measured_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("measured_at must include a timezone")
        return value

    @field_validator("consciousness")
    @classmethod
    def valid_consciousness(cls, value: str | None) -> str | None:
        allowed = {"ALERT", "NEW_CONFUSION", "VOICE", "PAIN", "UNRESPONSIVE"}
        if value is not None and value not in allowed:
            raise ValueError("Unsupported consciousness value")
        return value

    @field_validator("temperature")
    @classmethod
    def temperature_precision(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value.as_tuple().exponent < -1:
            raise ValueError("temperature supports one decimal place")
        return value

    @field_validator("supplemental_o2")
    @classmethod
    def oxygen_required_for_spo2(cls, value: bool | None, info):
        spo2 = info.data.get("spo2")
        if spo2 is not None and value is None:
            raise ValueError("supplemental_o2 is required when SpO2 is provided")
        return value

    def values(self) -> dict[str, object | None]:
        return {name: getattr(self, name) for name in (
            "respiration_rate", "spo2", "supplemental_o2", "systolic_bp",
            "pulse", "consciousness", "temperature",
        )}


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    admission_id: str
    measured_at: datetime
    received_at: datetime
    status: str
    idempotent_replay: bool = False
    plausibility_warnings: list[str] = Field(default_factory=list)
    respiration_rate: int | None = None
    spo2: int | None = None
    supplemental_o2: bool | None = None
    systolic_bp: int | None = None
    pulse: int | None = None
    consciousness: str | None = None
    temperature: Decimal | None = None
    source: str | None = None
    is_simulated: bool | None = None


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    patient_identifier: str
    age_years: int
    sex: str


class AdmissionResponse(BaseModel):
    id: str
    patient_id: str
    patient_identifier: str
    age_years: int
    sex: str
    ward_id: str
    ward_name: str
    bed_label: str
    admitted_at: datetime
    discharged_at: datetime | None
    spo2_scale: int
    status: str


class PageResponse(BaseModel):
    items: list[AdmissionResponse]
    limit: int
    offset: int
    total: int


class PatientPageResponse(BaseModel):
    items: list[PatientResponse]
    limit: int
    offset: int
    total: int


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    admission_id: str
    scoring_version: str
    observation_ids: list[str]
    per_parameter_scores: dict[str, int]
    completeness: int
    level: str
    total: int
    explanation: dict[str, object]
    computed_at: datetime
