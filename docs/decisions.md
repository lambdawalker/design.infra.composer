# Decision record

This index preserves design provenance without turning recommendations into accepted implementation choices. Dates below identify documentation records, not necessarily the date of the original discussion. Each future entry should include context, status, alternatives, rationale, affected documents and any superseded entry. Change status explicitly through review.

| ID / record date | Status | Decision / rationale |
|---|---|---|
| D001 / 2026-11-01 | Agreed requirement | Features declare contracts; applications integrate them. Declarations, deployment prerequisites and runtime relationships are distinct. See [architecture](architecture.md) |
| D002 / 2026-11-01 | Agreed requirement | Independent standalone panels are optional; integrated applications own configuration by default. Supersedes the exploratory common-JavaScript-shell direction |
| D003 / 2026-11-01 | Agreed requirement | Security, applicable provider recommendation, then cost. Supersedes unconditional env-variable preference; see [configuration](configuration-and-administration.md) |
| D004 / 2026-11-01 | Agreed requirement | Separate Application and Artifact settings; sensitivity/risk remains independent of category |
| D005 / 2026-11-01 | Recommended refinement | Explicit locked feature registration and deterministic matching; no hosted registry or general version solver required initially. Simpler reproducibility before dynamic discovery |
| D006 / 2026-11-01 | Recommended refinement | Preserve a logical plan/adapter boundary; Pulumi remains the current cloud target. A second executor is deferred until needed and independently verified |
| D007 / 2026-11-01 | Recommended refinement | Foundation bootstrap, bounded readiness, security mechanisms and test-evidence milestones refine existing requirements. No cloud implementation claim |

D005–D007 incorporate the [external-review assessment](validation-and-milestones.md). Remote discovery, final schema/API names, identity provider, vault backend and expanded version constraints remain open. Merging a design record does not by itself verify an implementation.
