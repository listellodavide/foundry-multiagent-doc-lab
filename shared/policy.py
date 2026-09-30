"""Contoso Creative vendor onboarding policy: the eight rules every lab checks.

The same text is printed into data/policy/vendor_onboarding_policy.pdf by the generator, so
agents can read the policy as a document, while code can apply it deterministically.
"""

from datetime import date
from typing import Literal

from shared.config import ONBOARDING_DATE
from shared.schema import DecisionRecord, Finding, KeyFacts, VendorProfile

RULES: dict[str, tuple[str, Literal["low", "medium", "high"], str]] = {
    "R1": ("Personal data breaches must be notified within 72 hours (DPA).", "high", "02_dpa.pdf"),
    "R2": ("The latest penetration test must be dated within 12 months before the onboarding date.", "medium", "03_security_questionnaire.pdf"),
    "R3": ("A SOC 2 Type II report must cover a period ending within 12 months before the onboarding date.", "medium", "03_security_questionnaire.pdf"),
    "R4": ("Cyber liability insurance must be at least EUR 1,000,000 and valid for at least 60 days after the onboarding date.", "medium", "04_insurance_certificate.pdf"),
    "R5": ("Payment terms must be 45 days or longer.", "low", "01_msa.pdf"),
    "R6": ("The vendor's liability cap must be at least 12 months of fees.", "high", "01_msa.pdf"),
    "R7": ("Invoice arithmetic must be correct: subtotal + VAT = total.", "low", "05_invoice.pdf"),
    "R8": ("The person who signed the MSA must be the authorised signatory in the company profile.", "high", "06_company_profile_scan.pdf"),
}

DECISION_RULE = (
    "approve when every rule passes; reject when two or more high-severity rules fail; "
    "otherwise conditional (onboarding may proceed once the failed rules are fixed)."
)


def policy_text() -> str:
    lines = [f"{rid} [{sev}] {text}" for rid, (text, sev, _) in RULES.items()]
    return "\n".join(lines) + f"\nOnboarding date: {ONBOARDING_DATE}\nDecision: {DECISION_RULE}"


def _within_previous_year(earlier: str | None, later: str) -> bool:
    if earlier is None:
        raise ValueError("Missing date")
    a, b = date.fromisoformat(earlier), date.fromisoformat(later)
    try:
        lower = b.replace(year=b.year - 1)
    except ValueError:  # Leap day: the preceding year's anniversary is February 28.
        lower = b.replace(year=b.year - 1, day=28)
    return lower <= a <= b


def judge(facts: KeyFacts, vendor: VendorProfile) -> list[Finding]:
    """Apply the policy in code. Missing facts give 'unknown', never a guess."""
    onboard = ONBOARDING_DATE

    def f(rule_id, ok, evidence):
        status = "unknown" if ok is None else ("pass" if ok else "fail")
        text, severity, source = RULES[rule_id]
        return Finding(rule_id=rule_id, status=status, severity=severity, evidence=evidence, source=source)

    def safe(check):
        try:
            return check()
        except (TypeError, ValueError):
            return None

    return [
        f("R1", safe(lambda: None if facts.breach_notification_hours is None else facts.breach_notification_hours <= 72), f"{facts.breach_notification_hours} hours"),
        f("R2", safe(lambda: _within_previous_year(facts.pen_test_date, onboard)), f"pen test {facts.pen_test_date}"),
        f("R3", safe(lambda: _within_previous_year(facts.soc2_report_date, onboard)), f"SOC 2 period end {facts.soc2_report_date}"),
        f("R4", safe(lambda: None if facts.insurance_cover_eur is None or facts.insurance_expiry is None
                     else facts.insurance_cover_eur >= 1_000_000
                     and (date.fromisoformat(facts.insurance_expiry) - date.fromisoformat(onboard)).days >= 60),
          f"EUR {facts.insurance_cover_eur}, expires {facts.insurance_expiry}"),
        f("R5", safe(lambda: None if facts.payment_terms_days is None else facts.payment_terms_days >= 45), f"net {facts.payment_terms_days} days"),
        f("R6", safe(lambda: None if facts.liability_cap_months is None else facts.liability_cap_months >= 12), f"cap {facts.liability_cap_months} months of fees"),
        f("R7", safe(lambda: None if facts.invoice_subtotal is None or facts.invoice_vat is None or facts.invoice_total is None
                     else abs(facts.invoice_subtotal + facts.invoice_vat - facts.invoice_total) < 0.01),
          f"{facts.invoice_subtotal} + {facts.invoice_vat} vs {facts.invoice_total}"),
        f("R8", None if not (facts.msa_signatory and vendor.signatory)
          else facts.msa_signatory.strip().lower() == vendor.signatory.strip().lower(),
          f"MSA signed by {facts.msa_signatory}; profile signatory {vendor.signatory}"),
    ]


def decide(findings: list[Finding]) -> Literal["approve", "conditional", "reject"]:
    high_fails = sum(1 for x in findings if x.status == "fail" and x.severity == "high")
    if all(x.status == "pass" for x in findings) and len(findings) == len(RULES):
        return "approve"
    return "reject" if high_fails >= 2 else "conditional"


def build_record(facts: KeyFacts, vendor: VendorProfile, rationale: str = "") -> DecisionRecord:
    findings = judge(facts, vendor)
    decision = decide(findings)
    if not rationale:
        failed = [x.rule_id for x in findings if x.status == "fail"]
        unknown = [x.rule_id for x in findings if x.status == "unknown"]
        rationale = f"Decision {decision}. Failed rules: {', '.join(failed) or 'none'}. Unknown: {', '.join(unknown) or 'none'}."
    return DecisionRecord(vendor=vendor, facts=facts, findings=findings, decision=decision, rationale=rationale)
