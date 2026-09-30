"""The output contract every lab produces: one DecisionRecord for the onboarding packet.

The models have no default values on purpose: OpenAI structured outputs in strict mode
require every property to be present, so optional values are expressed as "X | None".
"""

from typing import Literal

from pydantic import BaseModel, Field

RULE_IDS = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]


class VendorProfile(BaseModel):
    legal_name: str | None = Field(description="Registered company name")
    registration_number: str | None = Field(description="Trade register number, e.g. J40/12345/2019")
    country: str | None
    signatory: str | None = Field(description="Person authorised to sign contracts for the vendor")
    iban_last4: str | None = Field(description="Last 4 characters of the IBAN, never the full number")


class KeyFacts(BaseModel):
    breach_notification_hours: int | None = Field(description="Hours within which the vendor notifies a personal data breach")
    pen_test_date: str | None = Field(description="Date of the latest penetration test, ISO 8601")
    soc2_report_date: str | None = Field(description="End date of the latest SOC 2 Type II period, ISO 8601")
    insurance_cover_eur: int | None = Field(description="Cyber liability cover in EUR")
    insurance_expiry: str | None = Field(description="Insurance expiry date, ISO 8601")
    payment_terms_days: int | None
    liability_cap_months: int | None = Field(description="Vendor liability cap expressed in months of fees")
    msa_signatory: str | None = Field(description="Name of the person who signed the MSA for the vendor")
    invoice_subtotal: float | None
    invoice_vat: float | None
    invoice_total: float | None


class Finding(BaseModel):
    rule_id: str = Field(description="Policy rule id, R1 to R8")
    status: Literal["pass", "fail", "unknown"]
    severity: Literal["low", "medium", "high"]
    evidence: str = Field(description="Short quote or value taken from the document")
    source: str = Field(description="File name and page, e.g. '02_dpa.pdf p1'")


class DecisionRecord(BaseModel):
    vendor: VendorProfile
    facts: KeyFacts
    findings: list[Finding]
    decision: Literal["approve", "conditional", "reject"]
    rationale: str = Field(description="Two to four sentences a procurement officer can act on")


class RunRecord(BaseModel):
    """What a lab writes to out/: the model's record plus how it was produced."""
    technique: str
    runtime_s: float
    record: DecisionRecord
