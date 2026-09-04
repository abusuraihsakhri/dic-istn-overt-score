# DIC Istn Overt Score

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

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

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`score_platelets()`**: Score platelet count for ISTH Overt DIC.
Platelets in ×10³/µL.
  >100: 0 points
  50-100: 1 point
  <50: 2 points
- **`score_fibrin_marker()`**: Score fibrin degradation marker (D-dimer or FDP).
Accepts: 'no_increase', 'moderate_increase', 'strong_increase'
Or numeric fold-increase thresholds:
  No increase: <2× upper normal
  Moderate: 2-4× upper normal
  Strong: >4× upper normal
- **`score_pt_prolongation()`**: Score PT prolongation (seconds above upper limit of normal).
  <3s: 0 points
  3-6s: 1 point
  >6s: 2 points
- **`score_fibrinogen()`**: Score fibrinogen level in g/L.
  >1.0 g/L: 0 points
  ≤1.0 g/L: 1 point
- **`calculate_overt_dic_score()`**: Calculate the ISTH Overt DIC Score.

Args:
    platelets: Platelet count in ×10³/µL
    fibrin_marker: 'no_increase', 'moderate_increase', or 'strong_increase'
                   (or numeric fold-increase as string)
    pt_prolongation_seconds: PT prolongation in seconds above normal
    fibrinogen: Fibrinogen level in g/L

Returns:
    Dict with individual scores, total, and interpretation

---

## 📐 Mathematical Formulation & Logic

```text
  Calculate the ISTH Overt DIC Score.
  plt_score = score_platelets(platelets)
  fib_marker_score = score_fibrin_marker(fibrin_marker)
  pt_score = score_pt_prolongation(pt_prolongation_seconds)
  fg_score = score_fibrinogen(fibrinogen)
```

---

## 💻 CLI Quickstart & Usage

### 1. Calculate Overt DIC Score
```bash
python cli.py overt --platelets 80 --fibrin-marker moderate_increase --pt-prolongation 4 --fibrinogen 1.5
```

### 2. Calculate Non-Overt DIC Score (with trends)
```bash
python cli.py non-overt --platelets 90 --fibrin-marker moderate_increase --pt-prolongation 3 --fibrinogen 1.2 --platelet-trend falling
```

### 3. Get Clinical Context Guidance
```bash
python cli.py context --context sepsis --dic-score 6
```

### 4. Batch Process CSV
```bash
python cli.py batch -i input.csv -o results.csv
```

### 5. Audit Task Evaluation
```bash
python cli.py audit --task-id TASK-001
```

### 6. Query LLM Reasoning Adapter
```bash
python cli.py chat "Explain DIC scoring"
```

### 7. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### Parameter Reference
- `--platelets`: Specifies input measurement or parameter value.
- `--fibrin-marker`: Specifies input measurement or parameter value.
- `--pt-prolongation`: Specifies input measurement or parameter value.
- `--fibrinogen`: Specifies input measurement or parameter value.
- `--platelet-trend`: Specifies input measurement or parameter value.
- `--context`: Specifies input measurement or parameter value.
- `--dic-score`: Specifies input measurement or parameter value.
- `--fibrinogen-trend`: Specifies input measurement or parameter value.
- `--d-dimer-trend`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.

### Input Data Schema (Batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `platelets` | Platelet count (×10³/µL) | Required |
| `fibrin_marker` | Fibrin marker level: `no_increase`, `moderate_increase`, `strong_increase` (or numeric fold) | Required |
| `pt_prolongation` | PT prolongation in seconds above normal | Required |
| `fibrinogen` | Fibrinogen level (g/L) | Required |
| `score_type` | `overt` or `non_overt` (default: `overt`) | Optional |
| `platelet_trend` | `rising` or `falling` (for non-overt scoring) | Optional |
| `fibrinogen_trend` | `rising` or `falling` (for non-overt scoring) | Optional |
| `d_dimer_trend` | `rising` or `falling` (for non-overt scoring) | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOB patterns, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition. Requires `AUDIT_SECRET_KEY` environment variable (min 16 chars).
* **Path Traversal Protection:** Batch CSV processing validates file paths to prevent directory traversal attacks.
* **LLM Reasoning Adapter:** Deterministic mock implementation for clinical decision support queries.

### Environment Variables

| Variable | Required | Description |
|:---------|:---------|:------------|
| `AUDIT_SECRET_KEY` | Yes | HMAC secret key for audit trail (min 16 characters) |
| `MODEL_PROVIDER` | No | LLM provider: `mock`, `ollama`, `claude`, `openai` (default: `mock`) |

**Generate a secure key:**
```bash
# Linux/macOS
export AUDIT_SECRET_KEY=$(openssl rand -hex 32)

# Windows PowerShell
$env:AUDIT_SECRET_KEY = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
# Set test environment variable (tests configure this automatically)
pytest -v
```

Run specific test modules:

```bash
pytest tests/ -v          # Integration tests (agents, CLI, security)
pytest test_dic_istn.py -v  # Core scoring algorithm tests
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 100
```

---

## 🐳 Container Deployment

```bash
docker build -t dic-istn-overt-score .
docker run -e AUDIT_SECRET_KEY=your-secure-key dic-istn-overt-score
```

With Docker Compose:

```bash
docker-compose up -d
```

**Note:** The default `AUDIT_SECRET_KEY` in Docker is for development only. Override it in production:

```bash
docker run -e AUDIT_SECRET_KEY=$(openssl rand -hex 32) dic-istn-overt-score
```
