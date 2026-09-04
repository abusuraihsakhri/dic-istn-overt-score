"""
Automated Pytest Test Suite for Dic Istn Overt Score.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import os
import sys
from pathlib import Path

# Set required environment variable for audit trail before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-secret-key-for-unit-tests-2026")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_cli_audit_command():
    """Test the audit CLI subcommand returns valid JSON output."""
    from cli import main
    ret = main(["audit", "--task-id", "TEST-AUDIT-01"])
    assert ret == 0


def test_cli_chat_command():
    """Test the chat CLI subcommand processes queries."""
    from cli import main
    ret = main(["chat", "What", "is", "DIC"])
    assert ret == 0


def test_cli_verify_audit_command():
    """Test the verify-audit CLI subcommand checks integrity."""
    from cli import main
    ret = main(["verify-audit"])
    assert ret == 0


def test_path_traversal_protection():
    """Test that path traversal attempts are blocked in batch processing."""
    from dic_istn import _validate_safe_path
    import pytest

    # Path traversal should be blocked
    with pytest.raises(ValueError):
        _validate_safe_path("../../../etc/passwd")

    with pytest.raises(ValueError):
        _validate_safe_path("/etc/passwd")

    with pytest.raises(ValueError):
        _validate_safe_path("\\windows\\system32\\config\\sam")

    # Safe paths should work
    safe = _validate_safe_path("data/input.csv")
    assert safe.endswith("input.csv")


def test_audit_trail_requires_secret_key():
    """Test that AuditTrail requires a secret key."""
    from agents.base import AuditTrail
    import pytest

    # Save and clear the env var
    original_key = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        with pytest.raises(RuntimeError):
            AuditTrail()
    finally:
        # Restore the env var
        if original_key:
            os.environ["AUDIT_SECRET_KEY"] = original_key
        else:
            os.environ["AUDIT_SECRET_KEY"] = "test-secret-key-for-unit-tests-2026"


def test_audit_trail_rejects_short_key():
    """Test that AuditTrail rejects short secret keys."""
    from agents.base import AuditTrail
    import pytest

    with pytest.raises(RuntimeError):
        AuditTrail(secret_key="short")
