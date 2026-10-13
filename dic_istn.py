#!/usr/bin/env python3
"""
ISTH DIC (Disseminated Intravascular Coagulation) Score Calculator.

Implements:
  - ISTH Overt DIC Score (acute DIC)
  - Exploratory, non-validated non-overt DIC trend score

Overt DIC Scoring System (ISTH):
  Platelets (×10³/µL):  ≥100 → 0,  50-<100 → 1,  <50 → 2
  Fibrin marker (D-dimer/FDP):  No increase → 0,  Moderate increase → 2,  Strong increase → 3
  Prolonged PT (seconds above normal):  <3s → 0,  3-<6s → 1,  ≥6s → 2
  Fibrinogen (g/L):  ≥1.0 → 0,  <1.0 → 1

  Total ≥ 5: Compatible with overt DIC
  Total < 5: Not suggestive of overt DIC

Exploratory non-overt trend scoring:
  Retained for compatibility; NOT the published ISTH non-overt DIC template.

Clinical contexts: sepsis, trauma, obstetric emergencies, malignancy, snakebite.

Zero-dependency Python stdlib implementation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# Overt DIC Score
# ---------------------------------------------------------------------------

def _check_nonnegative_finite(value: float, label: str) -> None:
    """Reject nonsensical measurements, including NaN and infinity."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a finite non-negative number, got {value!r}")


def score_platelets(platelets: float) -> int:
    """
    Score platelet count for ISTH Overt DIC.
    Platelets in ×10³/µL.
      ≥100: 0 points
      50-<100: 1 point
      <50: 2 points
    """
    _check_nonnegative_finite(platelets, "Platelets")
    if platelets >= 100:
        return 0
    elif platelets >= 50:
        return 1
    else:
        return 2


def score_fibrin_marker(marker_level: str) -> int:
    """Score assay-interpreted fibrin markers; no universal D-dimer fold cutoff exists.

    The calling laboratory must establish what counts as moderately or strongly
    increased for its particular D-dimer/FDP assay and units. Numeric folds are
    deliberately rejected instead of using unsupported universal thresholds.
    """
    if not isinstance(marker_level, str):
        raise ValueError("Fibrin marker category must be a string")
    level = marker_level.strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "no_increase": 0,
        "none": 0,
        "normal": 0,
        "negative": 0,
        "moderate_increase": 2,
        "moderate": 2,
        "strong_increase": 3,
        "strong": 3,
        "marked": 3,
        "highly_positive": 3,
    }
    if level not in mapping:
        raise ValueError(
            "Fibrin marker must be no_increase, moderate_increase, or strong_increase "
            "using lab-validated assay interpretation; numeric folds and ambiguous "
            "positive results cannot be scored automatically"
        )
    return mapping[level]

def score_pt_prolongation(pt_prolongation_seconds: float) -> int:
    """
    Score PT prolongation (seconds above upper limit of normal).
      <3s: 0 points
      3-<6s: 1 point
      ≥6s: 2 points
    """
    _check_nonnegative_finite(pt_prolongation_seconds, "PT prolongation")
    if pt_prolongation_seconds < 3:
        return 0
    elif pt_prolongation_seconds < 6:
        return 1
    else:
        return 2


def score_fibrinogen(fibrinogen: float) -> int:
    """
    Score fibrinogen level in g/L.
      ≥1.0 g/L: 0 points
      <1.0 g/L: 1 point
    """
    _check_nonnegative_finite(fibrinogen, "Fibrinogen")
    if fibrinogen >= 1.0:
        return 0
    else:
        return 1


def calculate_overt_dic_score(
    platelets: float,
    fibrin_marker: str,
    pt_prolongation_seconds: float,
    fibrinogen: float,
) -> Dict[str, Any]:
    """
    Calculate the ISTH Overt DIC Score.

    Args:
        platelets: Platelet count in ×10³/µL
        fibrin_marker: 'no_increase', 'moderate_increase', or 'strong_increase'
                       after lab-validated assay interpretation
        pt_prolongation_seconds: PT prolongation in seconds above normal
        fibrinogen: Fibrinogen level in g/L

    Returns:
        Dict with individual scores, total, and interpretation
    """
    plt_score = score_platelets(platelets)
    fib_marker_score = score_fibrin_marker(fibrin_marker)
    pt_score = score_pt_prolongation(pt_prolongation_seconds)
    fg_score = score_fibrinogen(fibrinogen)

    total = plt_score + fib_marker_score + pt_score + fg_score

    if total >= 5:
        interpretation = "Compatible with overt DIC"
        recommendation = (
            "Score ≥ 5 is compatible with overt DIC only in a relevant clinical context. "
            "Assess the underlying cause and repeat laboratory scoring daily as appropriate."
        )
    else:
        interpretation = "Not suggestive of overt DIC"
        recommendation = (
            "Score < 5 is below the overt-DIC threshold, but does not exclude evolving coagulopathy. "
            "Interpret with a DIC-associated underlying condition and reassess clinically."
        )

    return {
        "score_type": "ISTH Overt DIC (categorical fibrin marker)",
        "platelets": platelets,
        "platelet_score": plt_score,
        "fibrin_marker": fibrin_marker,
        "fibrin_marker_score": fib_marker_score,
        "pt_prolongation_seconds": pt_prolongation_seconds,
        "pt_score": pt_score,
        "fibrinogen_g_per_L": fibrinogen,
        "fibrinogen_score": fg_score,
        "total_score": total,
        "max_possible_score": 8,
        "interpretation": interpretation,
        "overt_dic": total >= 5,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Non-Overt DIC Score (Chronic DIC)
# ---------------------------------------------------------------------------

def calculate_non_overt_dic_score(
    platelets: float,
    fibrin_marker: str,
    pt_prolongation_seconds: float,
    fibrinogen: float,
    platelet_trend: Optional[str] = None,
    fibrinogen_trend: Optional[str] = None,
    d_dimer_trend: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculate a legacy exploratory trend score (not a validated ISTH diagnostic score).

    The original ISTH non-overt scoring template is NOT the overt score plus
    these three trends. Preserve the historic output for backward compatibility
    while explicitly excluding diagnostic interpretation.

    The non-overt scoring adds dynamic components:
      - Rising platelet trend: -1 point (improving)
      - Falling platelet trend: +1 point (worsening)
      - Rising fibrinogen trend: -1 point (improving)
      - Falling fibrinogen trend: +1 point (worsening)
      - Rising D-dimer trend: +1 point (worsening)
      - Falling D-dimer trend: -1 point (improving)

    Args:
        platelets: Platelet count in ×10³/µL
        fibrin_marker: 'no_increase', 'moderate_increase', 'strong_increase'
        pt_prolongation_seconds: PT prolongation in seconds above normal
        fibrinogen: Fibrinogen level in g/L
        platelet_trend: 'rising', 'falling', or None
        fibrinogen_trend: 'rising', 'falling', or None
        d_dimer_trend: 'rising', 'falling', or None

    Returns:
        Dict with individual scores, total, dynamic score, and interpretation
    """
    # Base scores (same as overt)
    plt_score = score_platelets(platelets)
    fib_marker_score = score_fibrin_marker(fibrin_marker)
    pt_score = score_pt_prolongation(pt_prolongation_seconds)
    fg_score = score_fibrinogen(fibrinogen)

    base_total = plt_score + fib_marker_score + pt_score + fg_score

    # Dynamic scoring
    dynamic_score = 0
    dynamic_details = {}

    if platelet_trend:
        trend = platelet_trend.strip().lower()
        if trend == "rising":
            dynamic_score -= 1
            dynamic_details["platelet_dynamic"] = -1
        elif trend == "falling":
            dynamic_score += 1
            dynamic_details["platelet_dynamic"] = 1
        else:
            dynamic_details["platelet_dynamic"] = 0

    if fibrinogen_trend:
        trend = fibrinogen_trend.strip().lower()
        if trend == "rising":
            dynamic_score -= 1
            dynamic_details["fibrinogen_dynamic"] = -1
        elif trend == "falling":
            dynamic_score += 1
            dynamic_details["fibrinogen_dynamic"] = 1
        else:
            dynamic_details["fibrinogen_dynamic"] = 0

    if d_dimer_trend:
        trend = d_dimer_trend.strip().lower()
        if trend == "rising":
            dynamic_score += 1
            dynamic_details["d_dimer_dynamic"] = 1
        elif trend == "falling":
            dynamic_score -= 1
            dynamic_details["d_dimer_dynamic"] = -1
        else:
            dynamic_details["d_dimer_dynamic"] = 0

    total = base_total + dynamic_score

    if total >= 5:
        interpretation = "Exploratory trend score ≥5 (not diagnostic of non-overt DIC)"
        recommendation = (
            "This legacy trend sum is not a validated non-overt DIC algorithm. "
            "Evaluate the underlying disease and serial coagulation studies."
        )
    elif total >= 2:
        interpretation = "Exploratory evolving pattern (not diagnostic of non-overt DIC)"
        recommendation = (
            "An exploratory trend sum cannot establish non-overt DIC. "
            "Assess serial laboratory and clinical findings."
        )
    else:
        interpretation = "Exploratory trend score <2 (not diagnostic of non-overt DIC)"
        recommendation = "Do not use this exploratory score to rule out DIC."

    return {
        "score_type": "Exploratory non-overt DIC trend score (unvalidated)",
        "platelets": platelets,
        "platelet_score": plt_score,
        "fibrin_marker": fibrin_marker,
        "fibrin_marker_score": fib_marker_score,
        "pt_prolongation_seconds": pt_prolongation_seconds,
        "pt_score": pt_score,
        "fibrinogen_g_per_L": fibrinogen,
        "fibrinogen_score": fg_score,
        "base_score": base_total,
        "dynamic_score": dynamic_score,
        "dynamic_details": dynamic_details,
        "total_score": total,
        "max_possible_score": 11,
        "interpretation": interpretation,
        "dic_suggested": False,
        "validated_diagnostic_score": False,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Clinical Context Assessment
# ---------------------------------------------------------------------------

def assess_clinical_context(
    context: str,
    dic_score: int,
) -> Dict[str, Any]:
    """
    Provide clinical context-specific guidance for DIC.

    Supported contexts: sepsis, trauma, obstetric, malignancy, snakebite
    """
    context_lower = context.strip().lower()

    context_guidance = {
        "sepsis": {
            "description": "DIC in the setting of sepsis/septic shock",
            "key_considerations": [
                "Treat underlying infection with appropriate antimicrobials",
                "Follow current sepsis guidance; activated protein C (drotrecogin alfa) was withdrawn",
                "Platelet transfusion if < 10,000 or active bleeding",
                "Cryoprecipitate if fibrinogen < 100 mg/dL",
                "Heparin may be considered in thrombotic-predominant DIC",
            ],
            "mortality_implication": "DIC in sepsis is associated with increased mortality; risk varies by cohort",
        },
        "trauma": {
            "description": "DIC in the setting of major trauma (acute traumatic coagulopathy)",
            "key_considerations": [
                "Massive transfusion protocol with balanced ratio (1:1:1 RBC:FFP:Plt)",
                "Tranexamic acid within 3 hours of injury (CRASH-2 protocol)",
                "Correct hypothermia and acidosis (lethal triad)",
                "Fibrinogen replacement with cryoprecipitate",
                "Viscoelastic testing (TEG/ROTEM) to guide therapy",
            ],
            "mortality_implication": "Trauma-associated coagulopathy increases risk; prognosis depends on severity",
        },
        "obstetric": {
            "description": "DIC in obstetric emergencies (abruptio placentae, amniotic fluid embolism, PPH)",
            "key_considerations": [
                "Treat underlying cause (deliver placenta, control hemorrhage)",
                "Aggressive blood product replacement",
                "Fibrinogen replacement early (cryoprecipitate)",
                "Consider recombinant factor VIIa in refractory cases",
                "Uterine artery embolization or hysterectomy if needed",
            ],
            "mortality_implication": "Obstetric DIC requires rapid intervention; maternal mortality varies by cause",
        },
        "malignancy": {
            "description": "DIC in malignancy (often chronic/low-grade, especially APL)",
            "key_considerations": [
                "Acute promyelocytic leukemia (APL): all-trans retinoic acid (ATRA) immediately",
                "Low-grade DIC in solid tumors: treat underlying malignancy",
                "Thrombotic microangiopathy vs DIC: differentiate carefully",
                "LMWH for thrombotic-predominant picture",
                "Platelet and fibrinogen support as needed",
            ],
            "mortality_implication": "APL-associated DIC is a hematologic emergency",
        },
        "snakebite": {
            "description": "DIC from venom-induced consumptive coagulopathy",
            "key_considerations": [
                "Antivenom administration is the definitive treatment",
                "Monitor for anaphylaxis during antivenom infusion",
                "Blood product support for active hemorrhage",
                "DIC typically resolves rapidly with effective antivenom",
                "Avoid heparin — bleeding is the primary risk",
            ],
            "mortality_implication": "Prognosis depends on venom, severity, and time to effective treatment",
        },
    }

    if context_lower not in context_guidance:
        return {
            "context": context,
            "recognized": False,
            "guidance": f"Unknown clinical context '{context}'. Supported: {', '.join(context_guidance.keys())}",
        }

    guidance = context_guidance[context_lower]
    guidance["context"] = context_lower
    guidance["recognized"] = True
    guidance["dic_score"] = dic_score
    guidance["score_significant"] = dic_score >= 5

    return guidance


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def _validate_safe_path(file_path: str) -> str:
    """Resolve CLI input/output locations without falsely rejecting absolute paths.

    Explicit parent segments are disallowed as a conservative CLI guard.
    This is not a filesystem sandbox: OS file permissions remain authoritative.
    """
    import pathlib
    if not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("CSV path must be a nonempty string")
    if ".." in pathlib.PurePath(file_path).parts or (
        chr(92) in file_path or pathlib.PureWindowsPath(file_path).drive
    ):
        raise ValueError(f"Parent traversal or Windows network/drive path not supported: {file_path}")
    return str(pathlib.Path(file_path).resolve())


def _safe_csv_cell(value: Any) -> Any:
    """Prevent formulas from being executed if results are opened in a spreadsheet."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value

def process_batch(input_csv: str, output_csv: str) -> int:
    """
    Process a CSV of patient records and compute DIC scores.

    Expected columns: platelets, fibrin_marker, pt_prolongation, fibrinogen
    Optional: clinical_context, platelet_trend, fibrinogen_trend, d_dimer_trend, score_type

    Security: Validates file paths to prevent directory traversal attacks.
    """
    input_csv = _validate_safe_path(input_csv)
    output_csv = _validate_safe_path(output_csv)
    if input_csv == output_csv:
        raise ValueError("Input and output CSV paths must differ")

    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    required = {"platelets", "fibrin_marker", "pt_prolongation", "fibrinogen"}
    missing = required.difference(fieldnames)
    if missing:
        raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing))}")

    out_fields = list(dict.fromkeys(fieldnames + [
        "dic_total_score", "dic_interpretation", "overt_dic", "recommendation",
    ]))
    out_rows = []

    for r in rows:
        try:
            if None in r:
                raise ValueError("Unexpected extra CSV columns in row")
            platelets = float(r["platelets"])
            fibrin_marker = r["fibrin_marker"]
            pt_prolong = float(r["pt_prolongation"])
            fibrinogen = float(r["fibrinogen"])
            score_type = (r.get("score_type") or "overt").strip().lower()
            if score_type not in {"overt", "non_overt", "non-overt"}:
                raise ValueError(f"Invalid score_type: {score_type}")

            if score_type == "non_overt" or score_type == "non-overt":
                result = calculate_non_overt_dic_score(
                    platelets, fibrin_marker, pt_prolong, fibrinogen,
                    platelet_trend=r.get("platelet_trend"),
                    fibrinogen_trend=r.get("fibrinogen_trend"),
                    d_dimer_trend=r.get("d_dimer_trend"),
                )
            else:
                result = calculate_overt_dic_score(
                    platelets, fibrin_marker, pt_prolong, fibrinogen,
                )

            row_dict = {key: value for key, value in r.items() if key is not None}
            row_dict["dic_total_score"] = result["total_score"]
            row_dict["dic_interpretation"] = result["interpretation"]
            row_dict["overt_dic"] = result.get("overt_dic", result.get("dic_suggested", False))
            row_dict["recommendation"] = result["recommendation"]
        except (ValueError, KeyError, TypeError) as e:
            row_dict = {key: value for key, value in r.items() if key is not None}
            row_dict["dic_total_score"] = f"ERROR: {e}"
            row_dict["dic_interpretation"] = "ERROR"
            row_dict["overt_dic"] = ""
            row_dict["recommendation"] = ""

        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows({k: _safe_csv_cell(v) for k, v in row.items()} for row in out_rows)

    return len(out_rows)
