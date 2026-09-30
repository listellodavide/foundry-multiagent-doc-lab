"""Offline fixtures shared by the workshop solution tests."""

import pytest
from shared import config, pdf
from shared.schema import DecisionRecord
from tools.verify_offline import load_module


@pytest.fixture(scope="session", autouse=True)
def generate_packet(tmp_path_factory):
    # Isolate tests from PDFs being uploaded or read by a simultaneous live lab.
    root = tmp_path_factory.mktemp("workshop-packet")
    generator = load_module(config.ROOT / "data/generate_packet.py")
    setattr(generator, "ROOT", root)
    setattr(generator, "PACKET_DIR", root / "packet")
    setattr(generator, "POLICY_PDF", root / "policy" / "vendor_onboarding_policy.pdf")
    generator.main()
    with pytest.MonkeyPatch.context() as patch:
        for module in (config, pdf):
            patch.setattr(module, "PACKET_DIR", generator.PACKET_DIR)
            patch.setattr(module, "POLICY_PDF", generator.POLICY_PDF)
        yield


@pytest.fixture
def golden():
    return DecisionRecord.model_validate_json(config.GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture
def solution():
    def load(relative_path):
        return load_module(config.ROOT / "labs" / relative_path)
    return load
