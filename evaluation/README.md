# Evaluation methodology

## Scoped v1 acceptance benchmark

Run `python -m evaluation.benchmark --mode demo` from the repository root after `pip install -e ".[dev]"`. The 17-item [case file](cases.json) includes five in-scope conversion questions (including Chinese phrasing) and twelve deliberately unsupported questions (unavailable revenue/date/customer dimensions, unsupported causal claims, and dangerous instructions).

The benchmark reports supported-question end-to-end pass rate, unsupported-question rejection rate and overall pass rate. In-scope acceptance checks the output against the bundled **seed-42, 1,000-event** sample: sample size and exact event/conversion counts for each channel. An explicit unsupported-intent error counts as a correct rejection; infrastructure/HTTP/configuration errors do **not**. Other exceptions fail the case. A nonzero exit code indicates any failed case.

**Important:** `--mode demo` uses a fixed phrase matcher, so it does not measure LLM accuracy. `--mode openai` invokes an externally billed live model and has not been independently run or reported. Cases and expected aggregates are public and curated for one dataset; benchmark results must not be interpreted as independent statistical generalisation or BIRD/Spider scores. The aggregate count check does not establish full equivalence of arbitrary SQL queries. SQL attack handling is also tested separately by the regression suite.

## Regression tests

The regression suite uses synthetic marketing data and fixed reference cases for query restrictions, read-only execution, invalid data rejection, Wilson interval values, Holm corrections, sparse-count behavior, mocked provider responses, graph execution and HTTP behavior. These are correctness and regression checks, not natural-language SQL benchmarks.

## Future evaluation

- Create a held-out, versioned natural-language/expected SQL/expected-result corpus with multiple data distributions and semantic oracles.
- Report execution accuracy and unsupported-intent rejection rate across repeated live calls, model versions and prompt perturbations, including uncertainty intervals.
- Add BIRD/Spider adapters only if the agent's SQL/data contracts are extended appropriately; do not claim their scores until actually measured.
- Add user-level IDs and dependence-aware analysis to evaluate repeated-event statistical assumptions.
