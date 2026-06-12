"""Prescriptive advisory generation from signal state.

Maps STAMP diagnostic signals (IVI, NVD, SIG) to recommended control actions
for specific institutional controllers. This is the transition from
observational ("the control loop is broken") to prescriptive ("FAA should
issue a public statement within 48 hours").

The mapping follows STAMP's safety constraint derivation methodology:
signal conditions identify control failures, and prescriptions recommend
the control actions that would restore adequate control. Templates are
used (not LLM generation) so that every recommendation is traceable to
specific signal thresholds and STAMP failure modes.

No database dependency. I/O handled by storage.py and the CLI layer.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from .constants import (
    CAPTURE_RISK_INDEPENDENCE_THRESHOLD,
    CAPTURE_RISK_IVI_THRESHOLD,
    CAPTURE_RISK_NVD_THRESHOLD,
)
from .eval import CaptureRiskAlert, IviPoint

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControllerDef:
    """A STAMP controller loaded from controllers.yaml."""

    slug: str
    label: str
    role: str  # institutional | political | media | analyst
    stamp_function: str  # controller | actuator | sensor
    jurisdiction: str
    available_actions: list[dict[str, str]]
    information_needs: list[str]  # which signals: ivi, nvd, sig
    narratives: list[dict[str, str]]  # [{slug, relationship}]


@dataclass(frozen=True)
class AdvisoryRecord:
    """A generated prescriptive advisory for a specific controller."""

    controller_slug: str
    narrative_slug: str | None
    signal_trigger: str  # e.g. "ivi_vacuum", "nvd_divergence", "capture_risk"
    signal_values: dict[str, float]
    advisory_type: str  # act | investigate | monitor | disclose
    severity: str  # watch | advisory | alert
    recommendation: str
    rationale: str
    klein_activity: str | None
    stamp_failure_mode: str
    advisory_date: date


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------


@dataclass
class DomainConfig:
    """Domain-specific configuration for prescriptive advisory generation.

    Bundles the template strings, vocabulary, and signal names that vary
    across domains. The core advisory logic (threshold evaluation, severity
    scaling, controller filtering) is domain-agnostic. The templates that
    produce human-readable recommendations are domain-specific.

    Use INFORMATION_ENVIRONMENT for the default (TELL pipeline) or create
    a new DomainConfig for manufacturing, medical, or other domains.
    """

    # Signal type names used in this domain
    ivi_signal_name: str = "IVI"
    nvd_signal_name: str = "NVD"
    sig_signal_name: str = "SIG"

    # IVI templates
    ivi_controller_template: str = (
        "Issue public statement addressing discourse gap on this topic. "
        "Discourse volume exceeds institutional response by "
        "{ivi_value:.1f}x (threshold: {ivi_threshold:.1f}x). "
        "Sustained vacuum conditions increase narrative capture risk."
    )
    ivi_sensor_template: str = (
        "Information vacuum detected: discourse-to-institutional ratio "
        "is {ivi_value:.1f}x. Monitor for narrative capture conditions. "
        "Flag claims that lack institutional corroboration."
    )
    ivi_rationale_template: str = (
        "{signal_name} {ivi_value:.1f} on {date} "
        "exceeds threshold {ivi_threshold:.1f}. In STAMP terms, the "
        "controller ({controller_label}) is not issuing control actions "
        "proportional to the process excursion. "
        "Jurisdiction: {jurisdiction}."
    )

    # NVD templates
    nvd_originator_template: str = (
        "The '{narrative}' narrative you originated is "
        "spreading {nvd_value:.1f}x faster than supporting "
        "evidence. Release specific evidence or retract the claim. "
        "Narrative velocity: {narrative_velocity}, "
        "evidence velocity: {evidence_velocity}."
    )
    nvd_responder_template: str = (
        "The '{narrative}' narrative is outpacing evidence "
        "by {nvd_value:.1f}x. Release specific evidence or "
        "analysis addressing this narrative to close the gap. "
        "Narrative velocity: {narrative_velocity}, "
        "evidence velocity: {evidence_velocity}."
    )
    nvd_sensor_template: str = (
        "Narrative '{narrative}' spreading "
        "{nvd_value:.1f}x faster than evidence supports. "
        "Treat claims with proportional skepticism. "
        "Narrative velocity: {narrative_velocity}, "
        "evidence velocity: {evidence_velocity}."
    )

    # SIG templates
    sig_sensor_template: str = (
        "'{narrative}' is an echo chamber: independence "
        "score {independence_score:.0f}, amplification "
        "{amplification_ratio:.1f}x from single origin "
        "({origin_label}). Do not treat volume as "
        "corroboration. Verify source independence before "
        "amplifying claims."
    )
    sig_controller_template: str = (
        "'{narrative}' lacks independent corroboration. "
        "Independence score: {independence_score:.0f}. "
        "All {amplification_ratio:.0f} apparent sources trace "
        "to: {origin_label}. Do not base policy response on "
        "perceived volume."
    )

    # Capture risk templates
    capture_risk_controller_template: str = (
        "NARRATIVE CAPTURE RISK on '{narrative}'. "
        "Three signals converge: information vacuum (IVI "
        "{ivi_value:.1f}), narrative outpacing evidence "
        "(NVD {nvd_value:.2f}), echo amplification "
        "(independence {independence_score:.0f}, "
        "{amplification_ratio:.0f}x amplification). "
        "Risk score: {risk_score:.2f}. "
        "Prioritize evidence-based public response. Do not "
        "base policy on this narrative without independent "
        "verification."
    )
    capture_risk_sensor_template: str = (
        "NARRATIVE CAPTURE RISK on '{narrative}'. "
        "Composite risk score {risk_score:.2f}. "
        "IVI {ivi_value:.1f}, NVD {nvd_value:.2f}, "
        "independence {independence_score:.0f}. "
        "Structural conditions for narrative capture are present. "
        "Exercise maximum skepticism on this narrative."
    )

    # Entropy templates
    entropy_template: str = (
        "Premature closure risk: hypothesis entropy at "
        "{resistance_ratio:.0%} of maximum on "
        "{date}. "
        "Modal hypothesis: {modal_hypothesis}. "
        "Multiple competing explanations remain viable. Do not "
        "treat the dominant hypothesis as settled."
    )


# Default domain configuration for information environments (TELL)
INFORMATION_ENVIRONMENT = DomainConfig()

# Manufacturing domain configuration (for Omnissiah/OmniProject integration)
MANUFACTURING = DomainConfig(
    ivi_signal_name="Response Gap Index",
    nvd_signal_name="Assumption Drift Index",
    sig_signal_name="Supplier Independence Score",
    ivi_controller_template=(
        "Design requirements in this category exceed validated process "
        "coverage by {ivi_value:.1f}x (threshold: {ivi_threshold:.1f}x). "
        "Prioritize process qualification for unmatched requirements "
        "before committing manufacturing plan."
    ),
    ivi_sensor_template=(
        "Manufacturing knowledge gap detected: requirement-to-validated-process "
        "ratio is {ivi_value:.1f}x. Flag requirements that lack validated "
        "process coverage."
    ),
    ivi_rationale_template=(
        "{signal_name} {ivi_value:.1f} on {date} "
        "exceeds threshold {ivi_threshold:.1f}. The manufacturing library "
        "cannot characterize what is being asked. "
        "Controller ({controller_label}) should prioritize qualification. "
        "Jurisdiction: {jurisdiction}."
    ),
    nvd_originator_template=(
        "Process assumption '{narrative}' that you introduced is propagating "
        "{nvd_value:.1f}x faster than validation supports. "
        "Conduct independent testing or add explicit risk acceptance. "
        "Propagation count: {narrative_velocity}, "
        "validation count: {evidence_velocity}."
    ),
    nvd_responder_template=(
        "Process assumption '{narrative}' is propagating "
        "{nvd_value:.1f}x faster than validation data supports. "
        "Request independent test results before depending on this assumption. "
        "Propagation count: {narrative_velocity}, "
        "validation count: {evidence_velocity}."
    ),
    nvd_sensor_template=(
        "Assumption '{narrative}' propagating "
        "{nvd_value:.1f}x faster than validation supports. "
        "Flag as unvalidated in test reports. "
        "Propagation count: {narrative_velocity}, "
        "validation count: {evidence_velocity}."
    ),
    sig_sensor_template=(
        "Material/process qualification for '{narrative}' has independence "
        "score {independence_score:.0f}. All {amplification_ratio:.0f} "
        "certifications trace to: {origin_label}. "
        "Single-point failure risk. Require independent qualification path."
    ),
    sig_controller_template=(
        "Supplier qualification for '{narrative}' lacks independence. "
        "Score: {independence_score:.0f}. "
        "All {amplification_ratio:.0f} apparent qualifications trace "
        "to: {origin_label}. Do not treat redundancy as real."
    ),
    capture_risk_controller_template=(
        "MANUFACTURING SENSEMAKING ALERT on '{narrative}'. "
        "Three signals converge: knowledge gap (RGI "
        "{ivi_value:.1f}), assumption drift "
        "(ADI {nvd_value:.2f}), supplier echo "
        "(independence {independence_score:.0f}, "
        "{amplification_ratio:.0f}x). "
        "Risk score: {risk_score:.2f}. "
        "Hold manufacturing plan for independent review."
    ),
    capture_risk_sensor_template=(
        "MANUFACTURING SENSEMAKING ALERT on '{narrative}'. "
        "Composite risk score {risk_score:.2f}. "
        "RGI {ivi_value:.1f}, ADI {nvd_value:.2f}, "
        "independence {independence_score:.0f}. "
        "Do not release product without independent verification."
    ),
    entropy_template=(
        "Premature closure risk: failure-mode entropy at "
        "{resistance_ratio:.0%} of maximum on {date}. "
        "Dominant hypothesis: {modal_hypothesis}. "
        "Multiple root causes remain viable. Do not commit "
        "corrective action to a single failure mode."
    ),
)


# ---------------------------------------------------------------------------
# Controller loading
# ---------------------------------------------------------------------------


def load_controllers_yaml(yaml_path: Path) -> list[ControllerDef]:
    """Load controller definitions from YAML."""
    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    defs: list[ControllerDef] = []
    for c in raw.get("controllers", []):
        defs.append(
            ControllerDef(
                slug=c["slug"],
                label=c["label"],
                role=c["role"],
                stamp_function=c["stamp_function"],
                jurisdiction=c.get("jurisdiction", ""),
                available_actions=c.get("available_actions", []),
                information_needs=c.get("information_needs", []),
                narratives=c.get("narratives", []),
            )
        )
    return defs


# ---------------------------------------------------------------------------
# Prescription templates
# ---------------------------------------------------------------------------

# Each template maps a signal condition to a STAMP failure mode, recommended
# action, Klein sensemaking activity, and severity logic. Templates use
# string interpolation with signal values for auditability.


def _controller_needs_signal(controller: ControllerDef, signal: str) -> bool:
    """Check if a controller's information_needs include a signal type."""
    return signal in controller.information_needs


def _controller_narratives(controller: ControllerDef) -> dict[str, str]:
    """Return {narrative_slug: relationship} for a controller."""
    return {n["slug"]: n["relationship"] for n in controller.narratives}


# ---------------------------------------------------------------------------
# 1. IVI Vacuum advisories
# ---------------------------------------------------------------------------


def _generate_ivi_advisories(
    controllers: Sequence[ControllerDef],
    ivi_series: Sequence[IviPoint],
    *,
    ivi_threshold: float = CAPTURE_RISK_IVI_THRESHOLD,
    domain: DomainConfig = INFORMATION_ENVIRONMENT,
) -> list[AdvisoryRecord]:
    """Generate advisories when IVI exceeds threshold.

    STAMP failure: inadequate control action. The controller is not
    responding to a process excursion.
    """
    advisories: list[AdvisoryRecord] = []

    vacuum_days = [p for p in ivi_series if p.ivi_value >= ivi_threshold]

    for point in vacuum_days:
        for controller in controllers:
            if not _controller_needs_signal(controller, "ivi"):
                continue

            if point.ivi_value >= ivi_threshold * 3:
                severity = "alert"
            elif point.ivi_value >= ivi_threshold * 1.5:
                severity = "advisory"
            else:
                severity = "watch"

            tpl_vars = dict(
                ivi_value=point.ivi_value,
                ivi_threshold=ivi_threshold,
            )

            if controller.stamp_function == "controller":
                advisory_type = "act"
                recommendation = domain.ivi_controller_template.format(**tpl_vars)
            else:
                advisory_type = "monitor"
                recommendation = domain.ivi_sensor_template.format(**tpl_vars)

            rationale = domain.ivi_rationale_template.format(
                signal_name=domain.ivi_signal_name,
                ivi_value=point.ivi_value,
                ivi_threshold=ivi_threshold,
                date=point.window_end.isoformat(),
                controller_label=controller.label,
                jurisdiction=controller.jurisdiction,
            )

            advisories.append(
                AdvisoryRecord(
                    controller_slug=controller.slug,
                    narrative_slug=None,
                    signal_trigger="ivi_vacuum",
                    signal_values={"ivi": round(point.ivi_value, 2)},
                    advisory_type=advisory_type,
                    severity=severity,
                    recommendation=recommendation,
                    rationale=rationale,
                    klein_activity="Re-Framing",
                    stamp_failure_mode="inadequate_control_action",
                    advisory_date=point.window_end,
                )
            )

    return advisories


# ---------------------------------------------------------------------------
# 2. NVD Divergence advisories
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NvdSnapshot:
    """A single NVD observation for advisory generation."""

    narrative_slug: str
    window_end: date
    nvd_value: float
    narrative_velocity: int
    evidence_velocity: int


def _generate_nvd_advisories(
    controllers: Sequence[ControllerDef],
    nvd_points: Sequence[NvdSnapshot],
    *,
    nvd_threshold: float = CAPTURE_RISK_NVD_THRESHOLD,
    domain: DomainConfig = INFORMATION_ENVIRONMENT,
) -> list[AdvisoryRecord]:
    """Generate advisories when NVD exceeds threshold for a narrative.

    STAMP failure: process model divergence.
    """
    advisories: list[AdvisoryRecord] = []

    divergent = [p for p in nvd_points if p.nvd_value >= nvd_threshold]

    for point in divergent:
        for controller in controllers:
            if not _controller_needs_signal(controller, "nvd"):
                continue

            ctrl_narratives = _controller_narratives(controller)
            relationship = ctrl_narratives.get(point.narrative_slug)
            if relationship is None:
                continue

            if point.nvd_value >= nvd_threshold * 2:
                severity = "alert"
            elif point.nvd_value >= nvd_threshold * 1.3:
                severity = "advisory"
            else:
                severity = "watch"

            tpl_vars = dict(
                narrative=point.narrative_slug,
                nvd_value=point.nvd_value,
                narrative_velocity=point.narrative_velocity,
                evidence_velocity=point.evidence_velocity,
            )

            if controller.stamp_function == "controller":
                if relationship == "originator":
                    advisory_type = "disclose"
                    recommendation = domain.nvd_originator_template.format(**tpl_vars)
                elif relationship == "responder":
                    advisory_type = "disclose"
                    recommendation = domain.nvd_responder_template.format(**tpl_vars)
                else:
                    # monitor / amplifier roles on a STAMP controller get
                    # monitoring guidance, not "release evidence" directives
                    advisory_type = "monitor"
                    recommendation = domain.nvd_sensor_template.format(**tpl_vars)
            else:
                advisory_type = "monitor"
                recommendation = domain.nvd_sensor_template.format(**tpl_vars)

            rationale = (
                f"{domain.nvd_signal_name} {point.nvd_value:.2f} on "
                f"{point.window_end.isoformat()} for "
                f"'{point.narrative_slug}' exceeds threshold {nvd_threshold:.1f}. "
                f"In STAMP terms, the process model is diverging from "
                f"the process state. Controller {controller.label} "
                f"({relationship}) should act to realign."
            )

            advisories.append(
                AdvisoryRecord(
                    controller_slug=controller.slug,
                    narrative_slug=point.narrative_slug,
                    signal_trigger="nvd_divergence",
                    signal_values={"nvd": round(point.nvd_value, 2)},
                    advisory_type=advisory_type,
                    severity=severity,
                    recommendation=recommendation,
                    rationale=rationale,
                    klein_activity="Questioning",
                    stamp_failure_mode="process_model_divergence",
                    advisory_date=point.window_end,
                )
            )

    return advisories


# ---------------------------------------------------------------------------
# 3. SIG Echo Chamber advisories
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SigSnapshot:
    """A single SIG observation for advisory generation."""

    narrative_slug: str
    independence_score: float
    amplification_ratio: float
    origin_label: str


def _generate_sig_advisories(
    controllers: Sequence[ControllerDef],
    sig_results: Sequence[SigSnapshot],
    *,
    independence_threshold: float = CAPTURE_RISK_INDEPENDENCE_THRESHOLD,
    advisory_date: date | None = None,
    domain: DomainConfig = INFORMATION_ENVIRONMENT,
) -> list[AdvisoryRecord]:
    """Generate advisories when SIG independence falls below threshold.

    STAMP failure: sensor degradation.
    """
    advisories: list[AdvisoryRecord] = []

    echo_chambers = [s for s in sig_results if s.independence_score <= independence_threshold]

    for sig in echo_chambers:
        for controller in controllers:
            if not _controller_needs_signal(controller, "sig"):
                continue

            ctrl_narratives = _controller_narratives(controller)
            relationship = ctrl_narratives.get(sig.narrative_slug)
            if relationship is None:
                continue

            severity = "alert" if sig.independence_score <= 1 else "advisory"

            tpl_vars = dict(
                narrative=sig.narrative_slug,
                independence_score=sig.independence_score,
                amplification_ratio=sig.amplification_ratio,
                origin_label=sig.origin_label,
            )

            if controller.stamp_function == "sensor":
                advisory_type = "investigate"
                recommendation = domain.sig_sensor_template.format(**tpl_vars)
            else:
                advisory_type = "investigate"
                recommendation = domain.sig_controller_template.format(**tpl_vars)

            rationale = (
                f"{domain.sig_signal_name} independence "
                f"{sig.independence_score:.0f} for "
                f"'{sig.narrative_slug}' is at or below threshold "
                f"{independence_threshold:.0f}. In STAMP terms, the feedback "
                f"channel has {sig.independence_score:.0f} independent "
                f"sensor(s). The apparent redundancy is illusory."
            )

            the_date = advisory_date if advisory_date is not None else date.today()

            advisories.append(
                AdvisoryRecord(
                    controller_slug=controller.slug,
                    narrative_slug=sig.narrative_slug,
                    signal_trigger="sig_echo_chamber",
                    signal_values={
                        "sig_independence": round(sig.independence_score, 2),
                        "sig_amplification": round(sig.amplification_ratio, 2),
                    },
                    advisory_type=advisory_type,
                    severity=severity,
                    recommendation=recommendation,
                    rationale=rationale,
                    klein_activity="Connecting",
                    stamp_failure_mode="sensor_degradation",
                    advisory_date=the_date,
                )
            )

    return advisories


# ---------------------------------------------------------------------------
# 4. Composite capture risk advisories
# ---------------------------------------------------------------------------


def _generate_capture_risk_advisories(
    controllers: Sequence[ControllerDef],
    capture_alerts: Sequence[CaptureRiskAlert],
    *,
    domain: DomainConfig = INFORMATION_ENVIRONMENT,
) -> list[AdvisoryRecord]:
    """Generate advisories from composite capture-risk alerts.

    STAMP failure: unsafe control action preconditions.
    """
    advisories: list[AdvisoryRecord] = []

    for alert in capture_alerts:
        for controller in controllers:
            ctrl_narratives = _controller_narratives(controller)
            relationship = ctrl_narratives.get(alert.narrative_slug)
            if relationship is None:
                continue

            tpl_vars = dict(
                narrative=alert.narrative_slug,
                ivi_value=alert.ivi_value,
                nvd_value=alert.nvd_value,
                independence_score=alert.independence_score,
                amplification_ratio=alert.amplification_ratio,
                risk_score=alert.risk_score,
            )

            if controller.stamp_function == "controller":
                advisory_type = "act"
                recommendation = domain.capture_risk_controller_template.format(**tpl_vars)
            else:
                advisory_type = "monitor"
                recommendation = domain.capture_risk_sensor_template.format(**tpl_vars)

            rationale = (
                f"Composite capture-risk alert on {alert.alert_date.isoformat()} "
                f"for '{alert.narrative_slug}'. All three STAMP failure modes "
                f"converge: inadequate control action (IVI {alert.ivi_value:.1f} "
                f">= {CAPTURE_RISK_IVI_THRESHOLD}), process model divergence "
                f"(NVD {alert.nvd_value:.2f} >= {CAPTURE_RISK_NVD_THRESHOLD}), "
                f"and sensor degradation (independence "
                f"{alert.independence_score:.0f} <= "
                f"{CAPTURE_RISK_INDEPENDENCE_THRESHOLD}). "
                f"Risk score: {alert.risk_score:.2f}."
            )

            advisories.append(
                AdvisoryRecord(
                    controller_slug=controller.slug,
                    narrative_slug=alert.narrative_slug,
                    signal_trigger="capture_risk",
                    signal_values={
                        "ivi": round(alert.ivi_value, 2),
                        "nvd": round(alert.nvd_value, 2),
                        "sig_independence": round(alert.independence_score, 2),
                        "risk_score": round(alert.risk_score, 2),
                    },
                    advisory_type=advisory_type,
                    severity="alert",
                    recommendation=recommendation,
                    rationale=rationale,
                    klein_activity="Re-Framing",
                    stamp_failure_mode="unsafe_control_action_preconditions",
                    advisory_date=alert.alert_date,
                )
            )

    return advisories


# ---------------------------------------------------------------------------
# 5. Entropy / premature closure advisories
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EntropySnapshot:
    """A single day's entropy observation."""

    day: date
    entropy_bits: float
    resistance_ratio: float
    modal_hypothesis: str | None


def _generate_entropy_advisories(
    controllers: Sequence[ControllerDef],
    entropy_points: Sequence[EntropySnapshot],
    *,
    floor_ratio: float = 0.60,
    domain: DomainConfig = INFORMATION_ENVIRONMENT,
) -> list[AdvisoryRecord]:
    """Generate advisories when hypothesis entropy drops below floor.

    STAMP failure: premature model commitment.
    """
    advisories: list[AdvisoryRecord] = []

    low_entropy = [e for e in entropy_points if e.resistance_ratio < floor_ratio]

    for point in low_entropy:
        for controller in controllers:
            recommendation = domain.entropy_template.format(
                resistance_ratio=point.resistance_ratio,
                date=point.day.isoformat(),
                modal_hypothesis=point.modal_hypothesis or "unknown",
            )

            rationale = (
                f"Entropy {point.entropy_bits:.3f} bits "
                f"({point.resistance_ratio:.1%} of max) on "
                f"{point.day.isoformat()}. Klein's Comparing activity "
                f"requires maintaining multiple frames. Premature commitment "
                f"to a single hypothesis forecloses Re-Framing when new "
                f"evidence arrives."
            )

            advisories.append(
                AdvisoryRecord(
                    controller_slug=controller.slug,
                    narrative_slug=None,
                    signal_trigger="entropy_floor",
                    signal_values={
                        "entropy_bits": round(point.entropy_bits, 3),
                        "resistance_ratio": round(point.resistance_ratio, 3),
                    },
                    advisory_type="monitor",
                    severity="advisory",
                    recommendation=recommendation,
                    rationale=rationale,
                    klein_activity="Comparing",
                    stamp_failure_mode="premature_model_commitment",
                    advisory_date=point.day,
                )
            )

    return advisories


# ---------------------------------------------------------------------------
# Top-level advisory generation
# ---------------------------------------------------------------------------


def generate_advisories(
    controllers: Sequence[ControllerDef],
    *,
    ivi_series: Sequence[IviPoint] = (),
    nvd_points: Sequence[NvdSnapshot] = (),
    sig_results: Sequence[SigSnapshot] = (),
    capture_alerts: Sequence[CaptureRiskAlert] = (),
    entropy_points: Sequence[EntropySnapshot] = (),
    sig_advisory_date: date | None = None,
    ivi_threshold: float = CAPTURE_RISK_IVI_THRESHOLD,
    nvd_threshold: float = CAPTURE_RISK_NVD_THRESHOLD,
    independence_threshold: float = CAPTURE_RISK_INDEPENDENCE_THRESHOLD,
    entropy_floor: float = 0.60,
    domain: DomainConfig = INFORMATION_ENVIRONMENT,
) -> list[AdvisoryRecord]:
    """Generate all prescriptive advisories from current signal state.

    Combines IVI vacuum, NVD divergence, SIG echo chamber, composite
    capture risk, and entropy floor advisories. Returns a flat list
    sorted by date then severity.

    Pass a DomainConfig to generate advisories with domain-specific
    template language (e.g., MANUFACTURING for manufacturing composition).
    Defaults to INFORMATION_ENVIRONMENT (the TELL pipeline).
    """
    all_advisories: list[AdvisoryRecord] = []

    all_advisories.extend(
        _generate_ivi_advisories(
            controllers,
            ivi_series,
            ivi_threshold=ivi_threshold,
            domain=domain,
        )
    )
    all_advisories.extend(
        _generate_nvd_advisories(
            controllers,
            nvd_points,
            nvd_threshold=nvd_threshold,
            domain=domain,
        )
    )
    all_advisories.extend(
        _generate_sig_advisories(
            controllers,
            sig_results,
            independence_threshold=independence_threshold,
            advisory_date=sig_advisory_date,
            domain=domain,
        )
    )
    all_advisories.extend(
        _generate_capture_risk_advisories(
            controllers,
            capture_alerts,
            domain=domain,
        )
    )
    all_advisories.extend(
        _generate_entropy_advisories(
            controllers,
            entropy_points,
            floor_ratio=entropy_floor,
            domain=domain,
        )
    )

    # Sort by date, then severity (alert > advisory > watch)
    severity_order = {"alert": 0, "advisory": 1, "watch": 2}
    all_advisories.sort(
        key=lambda a: (a.advisory_date, severity_order.get(a.severity, 9)),
    )

    return all_advisories
