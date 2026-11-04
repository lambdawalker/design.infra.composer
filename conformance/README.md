# Portable conformance kit

Construct the scenarios below using the public API of your port. Each entry in [cases.json](cases.json) contains an input object and the expected public result. These are test messages. The library is free to expose classes, functions or another native API. A small test adapter reads one input object from stdin and writes one JSON result to stdout. Validation failures are expected results, so the adapter should return exit code zero when it can represent the error. Exceptions, crashes and malformed output fail the case.

Run all cases locally using Python 3 as the test driver. The implementation under test may use any language.

```sh
python3 conformance/check.py /path/to/your-adapter
# Interpreted adapter
python3 conformance/check.py python3 /path/to/adapter.py
```

Objects compare independent of key order. Arrays compare in order. Tests use synthetic identifiers, fixed clocks, in-memory state and mock prompts. Expected outputs were obtained from the Go reference at ad4cfd2. Passing these exercises is a starting interoperability check. Verify native SDK and teardown adapters separately with provider-specific mocks.

## Operations

- **plan** builds the named fixture and plans under the supplied environment, local account and local region. Return order, bindings and runtime_dependencies on success. On validation failure return deploymentStarted and the array of diagnostic codes.
- **selectSource** validates the supplied configuration declaration. Return the selected source name for the single binding or the first validation diagnostic code.
- **description** renders a mutable description for application app, deployment sample, the specified environment/domain/feature/owner, old purpose text and a 256-character limit.
- **approve** invokes the approval policy with the given kind and a positive routine timeout in timed mode. Simulate accept, reject, parent cancel, input failure or expiry of the policy's own timer. Return approved, rejected or stopped. An adapter can inject a controlled clock.
- **merge** normalizes and merges the supplied current and cached inventories, then writes a v1 report. Omitted input fields take their zero values. Use [the report schema](report-v1.schema.json) for the output and [the report protocol](../docs/artifact-reports.md) for evidence semantics.
- **state** reads the supplied synthetic Pulumi export at 2026-01-01T00:00:00Z and writes the resulting report with empty scope and metadata. The fixture deliberately includes unsafe or unsupported fields to test their omission.

## Planner fixture declarations

Use two v1 capability contracts. The first, example.user-pool, contains one string field id. The second, example.email-validator, contains one string field endpoint. All fields are public.

| Scenario | Construct these declarations |
|---|---|
| integrated | Register authentication and emailvalidation with no explicit injections. Authentication owns pool (kind example:user-pool, literal name example-users, string output id) and offers users from pool.id. It requires email-validator and declares a runtime use with reason “validate email when users register” and source “examples/authentication”. Emailvalidation requires users and owns validator (kind example:email-validator, input userPool from its users.id requirement, string output endpoint). It offers validator from that output. |
| auth | Register authentication alone with defaults enabled. Its default for email-validator is the test-only validator offering on auth-test-validator, supplied by resource auth-test-validator.validator with string output endpoint. |
| self / mutual | Register feature cycle. Each resource has kind example:cycle. In self, r000 explicitly depends on itself. In mutual, r000 depends on r001 and r001 depends on r000. Give each edge the reason “deliberate cycle demonstration”. |
| missing / ambiguous | Register consumer with one users requirement of example.user-pool and no default. For ambiguous only, add first and second, each offering users with literal id equal to its feature name. |

## Additional adapter acceptance tests

- Permute feature registration, nest references in inputs and introduce a forwarding cycle. Verify deterministic binding, prerequisite order, distinct reference/creation cycle diagnostics and zero factory calls on an invalid plan.
- Supply a secret to a resource through a nested or forwarded input. Verify taint through outputs and exports, redaction in public serialization and safe partial progress if a later factory fails.
- Simulate parent cancellation at the same instant as an approval timer, a wrapped timeout accompanied by an input failure, and an unanswered destructive prompt. Only a routine prompt's own unambiguous timeout can approve automatically.
- Feed a preview create, state recording and a partial read-only refresh in sequence. Verify exact physical identity, unchanged configuration timestamps, partial errors, a nested S3 object and a unique vs ambiguous parent relationship. Filter a child and verify that only its ancestor chain becomes context.
- Test destructive lifecycle with a fake driver. Verify environment-before-shared ordering, recovery blocking after incomplete inventory, and that fast check probes only previous REMAINS rows. Preserve skipped failure evidence.
