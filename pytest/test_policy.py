from datetime import date, timedelta

import pytest
from shared import config
from shared.policy import build_record, decide, judge
from shared.schema import KeyFacts, VendorProfile


def verdict(facts, vendor, rule):
    return next(f.status for f in judge(facts, vendor) if f.rule_id == rule)


def test_golden_policy(golden):
    record = build_record(golden.facts, golden.vendor)
    assert record.decision == "conditional"
    assert {f.rule_id for f in record.findings if f.status == "fail"} == {"R1", "R2", "R4", "R7"}


@pytest.mark.parametrize("field,rule,passing,failing", [
    ("breach_notification_hours", "R1", 72, 73),
    ("payment_terms_days", "R5", 45, 44),
    ("liability_cap_months", "R6", 12, 11),
])
def test_thresholds(golden, field, rule, passing, failing):
    assert verdict(golden.facts.model_copy(update={field: passing}), golden.vendor, rule) == "pass"
    assert verdict(golden.facts.model_copy(update={field: failing}), golden.vendor, rule) == "fail"
    assert verdict(golden.facts.model_copy(update={field: None}), golden.vendor, rule) == "unknown"


@pytest.mark.parametrize("field,rule", [("pen_test_date", "R2"), ("soc2_report_date", "R3")])
@pytest.mark.parametrize("value,expected", [
    ("2025-11-02", "pass"), ("2025-11-01", "fail"),
    ("2026-11-02", "pass"), ("2026-11-03", "fail"),
    ("not-a-date", "unknown"), (None, "unknown"),
])
def test_date_window(golden, field, rule, value, expected):
    assert verdict(golden.facts.model_copy(update={field: value}), golden.vendor, rule) == expected


@pytest.mark.parametrize("cover,days,expected", [
    (1_000_000, 60, "pass"), (999_999, 60, "fail"), (1_000_000, 59, "fail"),
    (None, 60, "unknown"), (1_000_000, None, "unknown"),
])
def test_insurance(golden, cover, days, expected):
    expiry = (date.fromisoformat(config.ONBOARDING_DATE) + timedelta(days=days)).isoformat() if days is not None else None
    facts = golden.facts.model_copy(update={"insurance_cover_eur": cover, "insurance_expiry": expiry})
    assert verdict(facts, golden.vendor, "R4") == expected


@pytest.mark.parametrize("total,expected", [(120.0, "pass"), (120.02, "fail"), (None, "unknown")])
def test_invoice(golden, total, expected):
    facts = golden.facts.model_copy(update={"invoice_subtotal": 100.0, "invoice_vat": 20.0, "invoice_total": total})
    assert verdict(facts, golden.vendor, "R7") == expected


def test_signatory_normalization(golden):
    facts = golden.facts.model_copy(update={"msa_signatory": "  IOANA MARINESCU "})
    assert verdict(facts, golden.vendor, "R8") == "pass"
    assert verdict(facts.model_copy(update={"msa_signatory": None}), golden.vendor, "R8") == "unknown"


def test_missing_facts():
    record = build_record(KeyFacts(**dict.fromkeys(KeyFacts.model_fields)),
                          VendorProfile(**dict.fromkeys(VendorProfile.model_fields)))
    assert {f.status for f in record.findings} == {"unknown"}
    assert record.decision == "conditional"


def test_decision_paths(golden):
    findings = [f.model_copy(update={"status": "pass"}) for f in golden.findings]
    assert decide(findings) == "approve"
    assert decide(findings[:-1]) == "conditional"
    findings[0] = findings[0].model_copy(update={"status": "fail"})
    assert decide(findings) == "conditional"
    findings[5] = findings[5].model_copy(update={"status": "fail"})
    assert decide(findings) == "reject"
