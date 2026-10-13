# ISTH Overt DIC Score Calculator

A deterministic calculator for the **classic categorical International Society on Thrombosis and Haemostasis (ISTH) overt disseminated intravascular coagulation (DIC) score**. It includes an offline browser interface, a standard-library Python calculator and CSV/CLI tools.

> **Clinical scope:** Educational and research use. Apply the overt-DIC score only in patients with a relevant underlying clinical condition. A score is not a standalone diagnosis and a value below 5 does not exclude evolving DIC. This implementation uses the classic categorical fibrin-marker classification; it does **not** implement the numeric D-dimer categories introduced in the 2025 ISTH update.

## Browser interface

The source-controlled site is in [web/index.html](web/index.html). Open that file directly in a modern browser for a fully local calculator, or publish the `web/` directory through the included GitHub Pages workflow.

- Requires platelet count (×10⁹/L or ×10³/µL), PT prolongation above the laboratory reference (seconds), fibrinogen (g/L), and an **assay-interpreted** fibrin-marker category.
- Requires confirmation that an underlying DIC-associated disorder is present.
- Shows total score (0–8), individual contributions, and a clinical interpretation.
- Offers a text summary download; no server requests, cookies, browser storage or third-party libraries are used.

The browser implementation uses plain JavaScript rather than Python-in-WebAssembly because the algorithm is small, deterministic and can run directly without downloading a Python runtime. The independent Python API remains available for batch analysis.

## Scoring scheme

| Component | 0 points | 1 point | 2 points | 3 points |
|---|---|---|---|---|
| Platelets (×10⁹/L) | ≥100 | 50–<100 | <50 | — |
| Fibrin-related marker | No increase | — | Moderate increase | Strong increase |
| PT prolongation (seconds) | <3 | ≥3 to <6 | ≥6 | — |
| Fibrinogen (g/L) | ≥1 | <1 | — | — |

**Total ≥5:** compatible with overt DIC in an appropriate clinical context. **Total <5:** below the threshold; clinical and serial laboratory assessment remains necessary.

**Fibrin-marker caution:** The older categorical algorithm does not define universal numeric D-dimer/FDP fold thresholds. The Python and browser implementations require a category established by the local laboratory. Values such as `"2.5"` and ambiguous `"positive"` are intentionally rejected.

### CLI examples

The deterministic scoring functions in `dic_istn.py` require no third-party packages. Python 3.10–3.12 is tested.

```bash
python cli.py overt --platelets 80 --fibrin-marker moderate_increase --pt-prolongation 4 --fibrinogen 0.9
python cli.py batch --input sample.csv --output results.csv
```

CSV input requires columns `platelets,fibrin_marker,pt_prolongation,fibrinogen`. The output includes total scores, interpretation and per-row errors. CSV result cells with spreadsheet-formula prefixes are escaped. The input and output paths must be different, and explicit parent-directory path segments are rejected; the CLI is not a filesystem sandbox.

The historical `non-overt` command is preserved for backward compatibility **only as an exploratory trend sum**. It does not implement the published ISTH non-overt DIC diagnostic template, must not be treated as a validated diagnostic score, and should not be used to rule in or rule out DIC. This distinction is also reflected in its output.

Other CLI commands include `context`, `audit`, `chat`, and `verify-audit`. The `chat` command uses a local deterministic **mock**, not a clinical reasoning model or a third-party inference API.

## Development and verification

```bash
python -m pip install 'fastapi>=0.111,<1' 'uvicorn>=0.30,<1' 'pydantic>=2,<3' pytest
export AUDIT_SECRET_KEY="$(openssl rand -hex 32)"
python -m pytest -v
node --check web/scoring.js
node --check web/app.js
node --test web/scoring.test.cjs
```

Python test coverage includes algorithm boundaries, numeric validity, batch input errors, a mock audit workflow, and HMAC integrity checks. The browser scoring test runner uses the Node.js built-in test framework. CI runs under Python 3.10, 3.11 and 3.12.

## Optional REST API

```bash
export AUDIT_SECRET_KEY="$(openssl rand -hex 32)"
uvicorn agents.api:app --host 127.0.0.1 --port 8000
```

The optional FastAPI service exposes `/health`, `/metrics`, `/api/audit`, `/api/chat`, and `/api/audit/logs`. This **generic mock audit service is separate from the DIC calculator**; it does not compute the ISTH score. It is not intended for public unauthenticated clinical use.

The audit log endpoint requires a separate `AUDIT_READ_TOKEN` environment variable and an `Authorization: Bearer <token>` header. If no read token is configured, that endpoint is disabled. The HMAC key must be at least 16 characters and should be generated cryptographically; audit history is held in process memory rather than persistent storage.

A local Docker configuration is provided:

```bash
export AUDIT_SECRET_KEY="$(openssl rand -hex 32)"
docker compose up --build
```

The Compose service listens on `127.0.0.1:8000` and does not ship with a default audit secret.

## Privacy and limitations

- The **browser calculator** processes user-entered laboratory values locally without transmitting or retaining them. Do not enter patient identifiers.
- The **Python CSV tool** reads and writes local files. Avoid PHI unless authorized and appropriately protected under institutional policy.
- The optional mock audit service includes limited regex checks for identifier-like strings, **not comprehensive PHI detection, anonymization or a HIPAA compliance guarantee**.
- Browser compatibility: current Chromium, Firefox, Safari and Edge supporting standard ES2017 JavaScript APIs. Browser automated rendering tests have not been added; scoring logic has direct Node.js regression tests.

## References

1. Taylor FB Jr, Toh CH, Hoots WK, Wada H, Levi M. Towards definition, clinical and laboratory criteria, and a scoring system for disseminated intravascular coagulation. *Thromb Haemost*. 2001;86:1327–1330. [PMID: 11816725](https://pubmed.ncbi.nlm.nih.gov/11816725/).
2. ISTH overt DIC scoring threshold table, reproduced in [Evaluation of the ISTH scoring system (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9629536/).
3. [Updated definition and scoring of DIC, ISTH SSC (2025)](https://www.jthjournal.org/article/S1538-7836%2825%2900220-X/fulltext). **The 2025 numeric fibrin marker revision is not implemented in this project.**
4. [Withdrawal of activated protein C in severe sepsis, NICE (2011)](https://www.nice.org.uk/guidance/ta84).

## License

MIT — see [LICENSE](LICENSE).
