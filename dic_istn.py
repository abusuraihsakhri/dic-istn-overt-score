#!/usr/bin/env python3
"""
ISTH DIC (Disseminated Intravascular Coagulation) Score Calculator.

Implements:
  - ISTH Overt DIC Score (acute DIC)
  - ISTH Non-Overt DIC Score (chronic/subclinical DIC)

Overt DIC Scoring System (ISTH):
  Platelets (×10³/µL):  >100 → 0,  50-100 → 1,  <50 → 2
  Fibrin marker (D-dimer/FDP):  No increase → 0,  Moderate increase → 2,  Strong increase → 3
  Prolonged PT (seconds above normal):  <3s → 0,  3-6s → 1,  >6s → 2
  Fibrinogen (g/L):  >1.0 → 0,  ≤1.0 → 1

  Total ≥ 5: Compatible with overt DIC
  Total < 5: Not suggestive of overt DIC

Non-Overt DIC Scoring (chronic):
  Uses same parameters plus dynamic changes over time.

Clinical contexts: sepsis, trauma, obstetric emergencies, malignancy, snakebite.

Zero-dependency Python stdlib implementation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import sys
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# Overt DIC Score
# ---------------------------------------------------------------------------

def score_platelets(platelets: float) -> int:
    """
    Score platelet count for ISTH Overt DIC.
    Platelets in ×10³/µL.
      >100: 0 points
      50-100: 1 point
      <50: 2 points
    """
    if platelets < 0:
        raise ValueError(f"Platelets must be non-negative, got {platelets}")
    if platelets > 100:
        return 0
    elif platelets >= 50:
        return 1
    else:
        return 2


def score_fibrin_marker(marker_level: str) -> int:
    """
    Score fibrin degradation marker (D-dimer or FDP).
    Accepts: 'no_increase', 'moderate_increase', 'strong_increase'
    Or numeric fold-increase thresholds:
      No increase: <2× upper normal
      Moderate: 2-4× upper normal
      Strong: >4× upper normal
    """
    level = marker_level.strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "no_increase": 0,
        "none": 0,
        "normal": 0,
        "negative": 0,
        "moderate_increase": 2,
        "moderate": 2,
        "positive": 2,
        "strong_increase": 3,
        "strong": 3,
        "marked": 3,
        "highly_positive": 3,
    }
    if level in mapping:
        return mapping[level]

    # Try numeric interpretation (fold-increase above upper normal)
    try:
        fold = float(marker_level)
        if fold < 2:
            return 0
        elif fold <= 4:
            return 2
        else:
            return 3
    except ValueError:
        raise ValueError(
            f"Unknown fibrin marker level: '{marker_level}'. "
            f"Use: no_increase, moderate_increase, strong_increase, or a numeric fold-increase."
        )


def score_pt_prolongation(pt_prolongation_seconds: float) -> int:
    """
    Score PT prolongation (seconds above upper limit of normal).
      <3s: 0 points
      3-6s: 1 point
      >6s: 2 points
    """
    if pt_prolongation_seconds < 0:
        raise ValueError(f"PT prolongation must be non-negative, got {pt_prolongation_seconds}")
    if pt_prolongation_seconds < 3:
        return 0
    elif pt_prolongation_seconds <= 6:
        return 1
    else:
        return 2


def score_fibrinogen(fibrinogen: float) -> int:
    """
    Score fibrinogen level in g/L.
      >1.0 g/L: 0 points
      ≤1.0 g/L: 1 point
    """
    if fibrinogen < 0:
        raise ValueError(f"Fibrinogen must be non-negative, got {fibrinogen}")
    if fibrinogen > 1.0:
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
                       (or numeric fold-increase as string)
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
            "ISTH score ≥ 5 supports diagnosis of overt DIC. "
            "Treat underlying cause; consider supportive transfusion if actively bleeding. "
            "Repeat scoring in 24 hours to monitor trajectory."
        )
    else:
        interpretation = "Not suggestive of overt DIC"
        recommendation = (
            "ISTH score < 5 does not support overt DIC diagnosis. "
            "If clinical suspicion remains, repeat testing in 24-48 hours."
        )

    return {
        "score_type": "ISTH Overt DIC",
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
    Calculate the ISTH Non-Overt DIC Score (chronic/subclinical DIC).

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
        interpretation = "Compatible with non-overt (chronic) DIC"
        recommendation = (
            "Non-overt DIC score ≥ 5. Treat underlying condition. "
            "Monitor coagulation parameters closely."
        )
    elif total >= 2:
        interpretation = "Suggestive of evolving non-overt DIC"
        recommendation = (
            "Score 2-4 suggests possible evolving DIC. "
            "Repeat testing and monitor trends."
        )
    else:
        interpretation = "Not suggestive of non-overt DIC"
        recommendation = "Score < 2 does not support DIC diagnosis."

    return {
        "score_type": "ISTH Non-Overt DIC",
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
        "dic_suggested": total >= 5,
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
                "Consider activated protein C (if available) in severe sepsis with DIC",
                "Platelet transfusion if < 10,000 or active bleeding",
                "Cryoprecipitate if fibrinogen < 100 mg/dL",
                "Heparin may be considered in thrombotic-predominant DIC",
            ],
            "mortality_implication": "DIC in sepsis doubles mortality risk",
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
            "mortality_implication": "Trauma-induced coagulopathy associated with 50%+ mortality",
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
            "mortality_implication": "Prognosis excellent with timely antivenom",
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

def process_batch(input_csv: str, output_csv: str) -> int:
    """
    Process a CSV of patient records and compute DIC scores.

    Expected columns: platelets, fibrin_marker, pt_prolongation, fibrinogen
    Optional: clinical_context, platelet_trend, fibrinogen_trend, d_dimer_trend, score_type
    """
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "dic_total_score", "dic_interpretation", "overt_dic", "recommendation",
    ]
    out_rows = []

    for r in rows:
        try:
            platelets = float(r.get("platelets", 150))
            fibrin_marker = r.get("fibrin_marker", "no_increase")
            pt_prolong = float(r.get("pt_prolongation", 0))
            fibrinogen = float(r.get("fibrinogen", 2.0))
            score_type = r.get("score_type", "overt").strip().lower()

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

            row_dict = dict(r)
            row_dict["dic_total_score"] = result["total_score"]
            row_dict["dic_interpretation"] = result["interpretation"]
            row_dict["overt_dic"] = result.get("overt_dic", result.get("dic_suggested", False))
            row_dict["recommendation"] = result["recommendation"]
        except (ValueError, KeyError) as e:
            row_dict = dict(r)
            row_dict["dic_total_score"] = f"ERROR: {e}"
            row_dict["dic_interpretation"] = "ERROR"
            row_dict["overt_dic"] = ""
            row_dict["recommendation"] = ""

        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    return len(out_rows)
