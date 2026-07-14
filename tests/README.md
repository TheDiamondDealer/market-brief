# Offline validation suite

This suite is the BR-01 safety baseline for the Big Remodel.

It deliberately uses committed fixtures and performs no network access. It covers:

- FRED CSV parsing and missing-observation handling;
- CFTC managed-money parsing plus an explicit unsafe-contract safety gate;
- House index discovery and hardened PTR row validation;
- Senate PTR HTML parsing;
- retained political-history merging;
- versioned generated-data schemas and semantic consistency;
- JavaScript syntax for generated browser caches;
- direct hash-route and script load-order contracts.

Run from the repository root:

```bash
python -m pip install requests beautifulsoup4 pdfplumber jsonschema
python scripts/validate_generated_data.py
python -m unittest discover -s tests -v
```

The unsafe COT-name helper is a testable gate for BR-06. BR-01 does not yet change the production contract-selection algorithm.
