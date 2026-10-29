# Evaluation scope

The current suite uses synthetic marketing data and fixed reference cases. It tests query restrictions, read-only execution, invalid data rejection, Wilson interval values, Holm corrections, sparse-count behavior, mocked provider responses, graph execution and HTTP behavior.

This is a correctness/regression suite, **not** a natural-language-to-SQL benchmark. No BIRD, Spider, real-user task success, deployment performance or model accuracy result is claimed. Add a versioned question/SQL/expected-result dataset before reporting model execution accuracy. Keep paid model runs opt-in and separate from CI.
