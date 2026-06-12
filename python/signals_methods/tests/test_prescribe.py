"""Unit tests for the prescriptive advisory engine.

Covers the five _generate_* functions (IVI, NVD, SIG, capture-risk, entropy),
severity bands, stamp-function role differentiation, narrative-relationship
handling, domain-config template substitution, and the top-level ordering
contract of generate_advisories(). No database, no filesystem, no YAML
loading: controllers and signal inputs are constructed in-process so failure
modes are isolated to the pure-Python prescriptive logic.

Three regressions from the PR 33 review cycle are covered directly:
    - non-responder narrative roles on an NVD controller get the sensor
      template, not the originator/responder disclose directive
      (commit 8a9ec86);
    - narrative_slug is carried through on NVD, SIG, and capture-risk
      advisories, and is None on IVI and entropy advisories (relevant to
      the narrative-dimension upsert key fix in commit 7ca111d);
    - MANUFACTURING DomainConfig overrides all six template classes, which
      is the contract the b57215e refactor was meant to guarantee.
"""

from __future__ import annotations

from datetime import date

from signals_methods.constants import (
    CAPTURE_RISK_INDEPENDENCE_THRESHOLD,
    CAPTURE_RISK_IVI_THRESHOLD,
    CAPTURE_RISK_NVD_THRESHOLD,
)
from signals_methods.eval import CaptureRiskAlert, IviPoint
from signals_methods.prescribe import (
    INFORMATION_ENVIRONMENT,
    MANUFACTURING,
    AdvisoryRecord,
    ControllerDef,
    EntropySnapshot,
    NvdSnapshot,
    SigSnapshot,
    _generate_capture_risk_advisories,
    _generate_entropy_advisories,
    _generate_ivi_advisories,
    _generate_nvd_advisories,
    _generate_sig_advisories,
    generate_advisories,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _controller(
    slug: str = "faa",
    label: str = "FAA",
    role: str = "institutional",
    stamp_function: str = "controller",
    jurisdiction: str = "US airspace",
    information_needs: tuple[str, ...] = ("ivi", "nvd", "sig"),
    narratives: tuple[tuple[str, str], ...] = (),
) -> ControllerDef:
    return ControllerDef(
        slug=slug,
        label=label,
        role=role,
        stamp_function=stamp_function,
        jurisdiction=jurisdiction,
        available_actions=[],
        information_needs=list(information_needs),
        narratives=[{"slug": s, "relationship": r} for s, r in narratives],
    )


D = date(2026, 1, 15)


# ---------------------------------------------------------------------------
# IVI advisories
# ---------------------------------------------------------------------------


def test_ivi_below_threshold_produces_no_advisory() -> None:
    ctrl = _controller(information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD - 0.1)]

    assert _generate_ivi_advisories([ctrl], points) == []


def test_ivi_at_threshold_produces_watch_severity() -> None:
    ctrl = _controller(information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD)]

    advisories = _generate_ivi_advisories([ctrl], points)

    assert len(advisories) == 1
    assert advisories[0].severity == "watch"


def test_ivi_above_1_5x_threshold_escalates_to_advisory() -> None:
    ctrl = _controller(information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD * 1.5)]

    advisories = _generate_ivi_advisories([ctrl], points)

    assert advisories[0].severity == "advisory"


def test_ivi_above_3x_threshold_escalates_to_alert() -> None:
    ctrl = _controller(information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD * 3)]

    advisories = _generate_ivi_advisories([ctrl], points)

    assert advisories[0].severity == "alert"


def test_ivi_skips_controllers_without_ivi_information_need() -> None:
    ctrl = _controller(information_needs=("nvd", "sig"))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD * 3)]

    assert _generate_ivi_advisories([ctrl], points) == []


def test_ivi_controller_role_produces_act_advisory_type() -> None:
    ctrl = _controller(stamp_function="controller", information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD)]

    a = _generate_ivi_advisories([ctrl], points)[0]

    assert a.advisory_type == "act"


def test_ivi_sensor_role_produces_monitor_advisory_type() -> None:
    ctrl = _controller(stamp_function="sensor", information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD)]

    a = _generate_ivi_advisories([ctrl], points)[0]

    assert a.advisory_type == "monitor"


def test_ivi_advisory_carries_no_narrative_slug() -> None:
    ctrl = _controller(information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD)]

    a = _generate_ivi_advisories([ctrl], points)[0]

    assert a.narrative_slug is None
    assert a.signal_trigger == "ivi_vacuum"
    assert a.klein_activity == "Re-Framing"
    assert a.stamp_failure_mode == "inadequate_control_action"


# ---------------------------------------------------------------------------
# NVD advisories
# ---------------------------------------------------------------------------


def test_nvd_below_threshold_produces_no_advisory() -> None:
    ctrl = _controller(
        information_needs=("nvd",),
        narratives=(("gov-coverup", "responder"),),
    )
    points = [
        NvdSnapshot(
            narrative_slug="gov-coverup",
            window_end=D,
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD - 0.1,
            narrative_velocity=5,
            evidence_velocity=10,
        )
    ]

    assert _generate_nvd_advisories([ctrl], points) == []


def test_nvd_skips_controllers_without_matching_narrative() -> None:
    ctrl = _controller(
        information_needs=("nvd",),
        narratives=(("foreign-aircraft", "responder"),),
    )
    points = [
        NvdSnapshot(
            narrative_slug="gov-coverup",
            window_end=D,
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD,
            narrative_velocity=10,
            evidence_velocity=5,
        )
    ]

    assert _generate_nvd_advisories([ctrl], points) == []


def test_nvd_originator_relationship_uses_originator_template() -> None:
    ctrl = _controller(
        stamp_function="controller",
        information_needs=("nvd",),
        narratives=(("gov-coverup", "originator"),),
    )
    points = [
        NvdSnapshot(
            narrative_slug="gov-coverup",
            window_end=D,
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD,
            narrative_velocity=15,
            evidence_velocity=3,
        )
    ]

    a = _generate_nvd_advisories([ctrl], points)[0]

    assert a.advisory_type == "disclose"
    assert "you originated" in a.recommendation


def test_nvd_responder_relationship_uses_responder_template() -> None:
    ctrl = _controller(
        stamp_function="controller",
        information_needs=("nvd",),
        narratives=(("gov-coverup", "responder"),),
    )
    points = [
        NvdSnapshot(
            narrative_slug="gov-coverup",
            window_end=D,
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD,
            narrative_velocity=15,
            evidence_velocity=3,
        )
    ]

    a = _generate_nvd_advisories([ctrl], points)[0]

    assert a.advisory_type == "disclose"
    assert "Release specific evidence or" in a.recommendation
    assert "you originated" not in a.recommendation


def test_nvd_non_responder_controller_role_uses_sensor_template() -> None:
    """Regression for commit 8a9ec86.

    A STAMP controller whose narrative relationship is neither originator nor
    responder (for example "monitor" or "amplifier") should receive the sensor
    template and the monitor advisory type, not a disclose directive that does
    not apply to its institutional role.
    """
    ctrl = _controller(
        stamp_function="controller",
        information_needs=("nvd",),
        narratives=(("gov-coverup", "monitor"),),
    )
    points = [
        NvdSnapshot(
            narrative_slug="gov-coverup",
            window_end=D,
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD,
            narrative_velocity=15,
            evidence_velocity=3,
        )
    ]

    a = _generate_nvd_advisories([ctrl], points)[0]

    assert a.advisory_type == "monitor"
    assert "Release" not in a.recommendation
    assert "you originated" not in a.recommendation


def test_nvd_sensor_function_always_uses_sensor_template() -> None:
    ctrl = _controller(
        stamp_function="sensor",
        information_needs=("nvd",),
        narratives=(("gov-coverup", "originator"),),
    )
    points = [
        NvdSnapshot(
            narrative_slug="gov-coverup",
            window_end=D,
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD,
            narrative_velocity=15,
            evidence_velocity=3,
        )
    ]

    a = _generate_nvd_advisories([ctrl], points)[0]

    assert a.advisory_type == "monitor"


def test_nvd_severity_bands() -> None:
    ctrl = _controller(
        information_needs=("nvd",),
        narratives=(("gov-coverup", "responder"),),
    )

    def _sev(multiplier: float) -> str:
        points = [
            NvdSnapshot(
                narrative_slug="gov-coverup",
                window_end=D,
                nvd_value=CAPTURE_RISK_NVD_THRESHOLD * multiplier,
                narrative_velocity=1,
                evidence_velocity=1,
            )
        ]
        return _generate_nvd_advisories([ctrl], points)[0].severity

    assert _sev(1.0) == "watch"
    assert _sev(1.3) == "advisory"
    assert _sev(2.0) == "alert"


def test_nvd_advisory_carries_narrative_slug() -> None:
    ctrl = _controller(
        information_needs=("nvd",),
        narratives=(("gov-coverup", "responder"),),
    )
    points = [
        NvdSnapshot(
            narrative_slug="gov-coverup",
            window_end=D,
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD,
            narrative_velocity=10,
            evidence_velocity=5,
        )
    ]

    a = _generate_nvd_advisories([ctrl], points)[0]

    assert a.narrative_slug == "gov-coverup"
    assert a.signal_trigger == "nvd_divergence"
    assert a.klein_activity == "Questioning"
    assert a.stamp_failure_mode == "process_model_divergence"


# ---------------------------------------------------------------------------
# SIG advisories
# ---------------------------------------------------------------------------


def test_sig_above_threshold_produces_no_advisory() -> None:
    ctrl = _controller(
        information_needs=("sig",),
        narratives=(("gov-coverup", "responder"),),
    )
    sigs = [
        SigSnapshot(
            narrative_slug="gov-coverup",
            independence_score=CAPTURE_RISK_INDEPENDENCE_THRESHOLD + 1,
            amplification_ratio=5.0,
            origin_label="nypost.com",
        )
    ]

    assert _generate_sig_advisories([ctrl], sigs) == []


def test_sig_at_threshold_produces_advisory_severity() -> None:
    ctrl = _controller(
        information_needs=("sig",),
        narratives=(("gov-coverup", "responder"),),
    )
    sigs = [
        SigSnapshot(
            narrative_slug="gov-coverup",
            independence_score=CAPTURE_RISK_INDEPENDENCE_THRESHOLD,
            amplification_ratio=5.0,
            origin_label="nypost.com",
        )
    ]

    a = _generate_sig_advisories([ctrl], sigs)[0]

    assert a.severity == "advisory"


def test_sig_independence_of_1_or_less_escalates_to_alert() -> None:
    ctrl = _controller(
        information_needs=("sig",),
        narratives=(("gov-coverup", "responder"),),
    )
    sigs = [
        SigSnapshot(
            narrative_slug="gov-coverup",
            independence_score=1.0,
            amplification_ratio=10.0,
            origin_label="nypost.com",
        )
    ]

    a = _generate_sig_advisories([ctrl], sigs)[0]

    assert a.severity == "alert"


def test_sig_sensor_and_controller_roles_use_different_templates() -> None:
    sensor_ctrl = _controller(
        slug="media-ref",
        stamp_function="sensor",
        information_needs=("sig",),
        narratives=(("gov-coverup", "responder"),),
    )
    inst_ctrl = _controller(
        slug="faa",
        stamp_function="controller",
        information_needs=("sig",),
        narratives=(("gov-coverup", "responder"),),
    )
    sigs = [
        SigSnapshot(
            narrative_slug="gov-coverup",
            independence_score=1.0,
            amplification_ratio=12.0,
            origin_label="nypost.com",
        )
    ]

    sensor_a = _generate_sig_advisories([sensor_ctrl], sigs)[0]
    ctrl_a = _generate_sig_advisories([inst_ctrl], sigs)[0]

    assert sensor_a.recommendation != ctrl_a.recommendation
    assert "echo chamber" in sensor_a.recommendation
    assert "policy response" in ctrl_a.recommendation


def test_sig_uses_provided_advisory_date() -> None:
    ctrl = _controller(
        information_needs=("sig",),
        narratives=(("gov-coverup", "responder"),),
    )
    sigs = [
        SigSnapshot(
            narrative_slug="gov-coverup",
            independence_score=1.0,
            amplification_ratio=10.0,
            origin_label="nypost.com",
        )
    ]

    a = _generate_sig_advisories([ctrl], sigs, advisory_date=D)[0]

    assert a.advisory_date == D


def test_sig_skips_controllers_without_matching_narrative() -> None:
    ctrl = _controller(
        information_needs=("sig",),
        narratives=(("other-story", "responder"),),
    )
    sigs = [
        SigSnapshot(
            narrative_slug="gov-coverup",
            independence_score=1.0,
            amplification_ratio=10.0,
            origin_label="nypost.com",
        )
    ]

    assert _generate_sig_advisories([ctrl], sigs) == []


# ---------------------------------------------------------------------------
# Composite capture-risk advisories
# ---------------------------------------------------------------------------


def test_capture_risk_skips_controllers_without_matching_narrative() -> None:
    ctrl = _controller(narratives=(("other-story", "responder"),))
    alerts = [
        CaptureRiskAlert(
            alert_date=D,
            narrative_slug="gov-coverup",
            ivi_value=6.0,
            nvd_value=1.5,
            independence_score=1.0,
            amplification_ratio=20.0,
            risk_score=0.85,
        )
    ]

    assert _generate_capture_risk_advisories([ctrl], alerts) == []


def test_capture_risk_controller_produces_act_alert() -> None:
    ctrl = _controller(
        stamp_function="controller",
        narratives=(("gov-coverup", "responder"),),
    )
    alerts = [
        CaptureRiskAlert(
            alert_date=D,
            narrative_slug="gov-coverup",
            ivi_value=6.0,
            nvd_value=1.5,
            independence_score=1.0,
            amplification_ratio=20.0,
            risk_score=0.85,
        )
    ]

    a = _generate_capture_risk_advisories([ctrl], alerts)[0]

    assert a.advisory_type == "act"
    assert a.severity == "alert"
    assert a.signal_trigger == "capture_risk"
    assert a.klein_activity == "Re-Framing"
    assert a.stamp_failure_mode == "unsafe_control_action_preconditions"


def test_capture_risk_sensor_produces_monitor_alert() -> None:
    ctrl = _controller(
        stamp_function="sensor",
        narratives=(("gov-coverup", "responder"),),
    )
    alerts = [
        CaptureRiskAlert(
            alert_date=D,
            narrative_slug="gov-coverup",
            ivi_value=6.0,
            nvd_value=1.5,
            independence_score=1.0,
            amplification_ratio=20.0,
            risk_score=0.85,
        )
    ]

    a = _generate_capture_risk_advisories([ctrl], alerts)[0]

    assert a.advisory_type == "monitor"
    assert a.severity == "alert"


# ---------------------------------------------------------------------------
# Entropy / premature-closure advisories
# ---------------------------------------------------------------------------


def test_entropy_above_floor_produces_no_advisory() -> None:
    ctrl = _controller()
    points = [
        EntropySnapshot(
            day=D,
            entropy_bits=2.0,
            resistance_ratio=0.85,
            modal_hypothesis="H3",
        )
    ]

    assert _generate_entropy_advisories([ctrl], points) == []


def test_entropy_below_floor_produces_advisory_for_every_controller() -> None:
    ctrls = [
        _controller(slug="faa", information_needs=()),
        _controller(slug="dhs", information_needs=("ivi",)),
    ]
    points = [
        EntropySnapshot(
            day=D,
            entropy_bits=0.5,
            resistance_ratio=0.25,
            modal_hypothesis="H3",
        )
    ]

    advisories = _generate_entropy_advisories(ctrls, points)

    assert len(advisories) == 2
    assert {a.controller_slug for a in advisories} == {"faa", "dhs"}
    assert all(a.severity == "advisory" for a in advisories)
    assert all(a.advisory_type == "monitor" for a in advisories)
    assert all(a.signal_trigger == "entropy_floor" for a in advisories)
    assert all(a.klein_activity == "Comparing" for a in advisories)


def test_entropy_advisory_carries_no_narrative_slug() -> None:
    ctrl = _controller()
    points = [
        EntropySnapshot(
            day=D,
            entropy_bits=0.5,
            resistance_ratio=0.25,
            modal_hypothesis=None,
        )
    ]

    a = _generate_entropy_advisories([ctrl], points)[0]

    assert a.narrative_slug is None
    assert "unknown" in a.recommendation


# ---------------------------------------------------------------------------
# Top-level generate_advisories orchestration
# ---------------------------------------------------------------------------


def test_generate_advisories_sorts_by_date_then_severity() -> None:
    ctrl = _controller(
        information_needs=("ivi", "nvd"),
        narratives=(("gov-coverup", "responder"),),
    )

    # Two IVI points on different days, second one with a higher severity.
    ivi = [
        IviPoint(
            window_end=date(2026, 1, 20),
            ivi_value=CAPTURE_RISK_IVI_THRESHOLD * 3,  # alert
        ),
        IviPoint(
            window_end=date(2026, 1, 10),
            ivi_value=CAPTURE_RISK_IVI_THRESHOLD,  # watch
        ),
    ]
    # Two NVD points: same later day as the alert-severity IVI, both advisory.
    nvd = [
        NvdSnapshot(
            narrative_slug="gov-coverup",
            window_end=date(2026, 1, 20),
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD * 1.5,  # advisory
            narrative_velocity=10,
            evidence_velocity=3,
        )
    ]

    result = generate_advisories([ctrl], ivi_series=ivi, nvd_points=nvd, sig_advisory_date=D)

    dates_and_severities = [(a.advisory_date, a.severity) for a in result]

    assert dates_and_severities == sorted(
        dates_and_severities,
        key=lambda ds: (ds[0], {"alert": 0, "advisory": 1, "watch": 2}.get(ds[1], 9)),
    )
    # Earlier date comes first regardless of severity difference
    assert result[0].advisory_date == date(2026, 1, 10)
    # Among same-date results, alert precedes advisory
    same_day = [a for a in result if a.advisory_date == date(2026, 1, 20)]
    assert same_day[0].severity == "alert"


def test_generate_advisories_returns_empty_for_no_input() -> None:
    ctrl = _controller()

    assert generate_advisories([ctrl]) == []


def test_generate_advisories_returns_advisory_records() -> None:
    ctrl = _controller(information_needs=("ivi",))
    ivi = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD)]

    result = generate_advisories([ctrl], ivi_series=ivi)

    assert len(result) == 1
    assert isinstance(result[0], AdvisoryRecord)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------


def test_information_environment_ivi_uses_ivi_signal_name() -> None:
    ctrl = _controller(information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD)]

    a = _generate_ivi_advisories([ctrl], points, domain=INFORMATION_ENVIRONMENT)[0]

    assert "IVI " in a.rationale


def test_manufacturing_ivi_uses_response_gap_index_signal_name() -> None:
    ctrl = _controller(information_needs=("ivi",))
    points = [IviPoint(window_end=D, ivi_value=CAPTURE_RISK_IVI_THRESHOLD)]

    a = _generate_ivi_advisories([ctrl], points, domain=MANUFACTURING)[0]

    assert "Response Gap Index" in a.rationale
    assert "IVI " not in a.rationale


def test_manufacturing_nvd_uses_assumption_drift_language() -> None:
    ctrl = _controller(
        stamp_function="controller",
        information_needs=("nvd",),
        narratives=(("weldability", "originator"),),
    )
    points = [
        NvdSnapshot(
            narrative_slug="weldability",
            window_end=D,
            nvd_value=CAPTURE_RISK_NVD_THRESHOLD,
            narrative_velocity=10,
            evidence_velocity=3,
        )
    ]

    a = _generate_nvd_advisories([ctrl], points, domain=MANUFACTURING)[0]

    assert "Process assumption" in a.recommendation
    assert "propagating" in a.recommendation


def test_manufacturing_capture_risk_uses_manufacturing_alert_language() -> None:
    ctrl = _controller(
        stamp_function="controller",
        narratives=(("weldability", "responder"),),
    )
    alerts = [
        CaptureRiskAlert(
            alert_date=D,
            narrative_slug="weldability",
            ivi_value=6.0,
            nvd_value=1.5,
            independence_score=1.0,
            amplification_ratio=3.0,
            risk_score=0.85,
        )
    ]

    a = _generate_capture_risk_advisories([ctrl], alerts, domain=MANUFACTURING)[0]

    assert "MANUFACTURING SENSEMAKING ALERT" in a.recommendation
    assert "Hold manufacturing plan" in a.recommendation


def test_manufacturing_entropy_uses_failure_mode_language() -> None:
    ctrl = _controller()
    points = [
        EntropySnapshot(
            day=D,
            entropy_bits=0.5,
            resistance_ratio=0.25,
            modal_hypothesis="material-defect",
        )
    ]

    a = _generate_entropy_advisories([ctrl], points, domain=MANUFACTURING)[0]

    assert "failure-mode entropy" in a.recommendation
    assert "corrective action" in a.recommendation
