# DIC — ISTH Disseminated Intravascular Coagulation Score Calculator

A zero-dependency Python tool implementing the ISTH (International Society on Thrombosis and Haemostasis) scoring systems for Disseminated Intravascular Coagulation (DIC).

## Scoring Systems

### ISTH Overt DIC Score (Acute)

| Parameter | Value | Score |
|-----------|-------|-------|
| Platelets (×10³/µL) | > 100 | 0 |
| | 50 – 100 | 1 |
| | < 50 | 2 |
| Fibrin marker (D-dimer/FDP) | No increase | 0 |
| | Moderate increase | 2 |
| | Strong increase | 3 |
| PT prolongation (seconds) | < 3 | 0 |
| | 3 – 6 | 1 |
| | > 6 | 2 |
| Fibrinogen (g/L) | > 1.0 | 0 |
| | ≤ 1.0 | 1 |

**Interpretation:** Total ≥ 5 → Compatible with overt DIC. Total < 5 → Not suggestive.

### ISTH Non-Overt DIC Score (Chronic)

Adds dynamic trend scoring on top of the base score:
- Falling platelets: +1 | Rising platelets: −1
- Falling fibrinogen: +1 | Rising fibrinogen: −1
- Rising D-dimer: +1 | Falling D-dimer: −1

## Clinical Contexts

The tool provides context-specific guidance for:
- **Sepsis** — antimicrobials, activated protein C, transfusion thresholds
- **Trauma** — massive transfusion protocol, TXA, lethal triad management
- **Obstetric** — delivery, cryoprecipitate, rFVIIa
- **Malignancy** — APL (ATRA), LMWH for thrombotic DIC
- **Snakebite** — antivenom as definitive treatment

## Quick Start

### CLI

```bash
# Overt DIC score
python cli.py overt --platelets 80 --fibrin-marker moderate_increase \
    --pt-prolongation 4 --fibrinogen 0.9

# Non-Overt DIC score with trends
python cli.py non-overt --platelets 90 --fibrin-marker moderate_increase \
    --pt-prolongation 3 --fibrinogen 1.2 --platelet-trend falling

# Clinical context guidance
python cli.py context --context sepsis --dic-score 6

# Batch processing
python cli.py batch -i patients.csv -o results.csv
```

### Python API

```python
from dic_istn import calculate_overt_dic_score, assess_clinical_context

result = calculate_overt_dic_score(
    platelets=40,
    fibrin_marker="strong_increase",
    pt_prolongation_seconds=5.0,
    fibrinogen=0.8,
)
print(result["total_score"])    # 7
print(result["overt_dic"])      # True
```

## Running Tests

```bash
python -m pytest test_dic_istn.py -v
```

## License

MIT License.
