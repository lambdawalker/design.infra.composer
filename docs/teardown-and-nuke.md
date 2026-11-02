# All-environment teardown, nuke and follow-up verification

## Status and intent

**Agreed:** provide an explicitly authorized nuke operation that attempts every application environment, then the shared admin/index control plane. Continue independent cleanup after failures, count confirmed missing artifacts as success, and report exactly what was deleted, remains, was retained or could not be verified. Recovery state and encryption keys are processed last and only after earlier cleanup is verified.

**Implemented reference:** [go.infra.composer](https://github.com/lambdawalker/go.infra.composer) provides the dependency-free `teardown` engine, installed Pulumi/AWS CLI driver and `infra-nuke` command. [go.attestra.aws](https://github.com/lambdawalker/go.attestra.aws) integrates that engine into its operator workflow. Implementation evidence is recorded in [Composer #3](https://github.com/lambdawalker/go.infra.composer/pull/3), [Composer #4](https://github.com/lambdawalker/go.infra.composer/pull/4) and [Attestra #5](https://github.com/lambdawalker/go.attestra.aws/pull/5). These changes were validated with tests, fake process runners and builds; they do not establish live AWS cleanup results.

This lifecycle is separate from ordinary environment teardown, release retirement, feature runtime reset and a configuration Save. It removes application data within its adopted scope. The current reference exposes CLI operations; a hosted admin nuke panel, durable hosted worker and account-wide deployment coordinator are not implied.

## 1. Ownership and scope

| Owner | Responsibility |
|---|---|
| Composer | Reusable phase ordering, inventory persistence, per-artifact verification, retries, recovery gate and full/fast checks |
| Application | Adopted projects/backends, all-environment discovery, shared admin/index classification, operator credentials/authorization and cleanup outside Pulumi |
| Feature | Native resource declarations and safe ownership metadata; no application-wide admin/index teardown dependency |
| Embedding operator/worker | Deployment suspension, coordination, protected report location and explicitly approved recovery ownership |

Applications register all owned environment projects/backends and mark shared control-plane projects separately. In Attestra these are `attestra-application` and `attestra-control-plane`; those names are application choices, not Composer constants. Admin and index may be separate shared targets. A standalone feature can use the same engine/CLI with its isolated project/backend configuration without importing the application or deploying its control plane.

The generic driver discovers stacks within explicitly configured projects/backends and combines them with saved retry targets. The application adapter may obtain that configuration from repository environment variables, local setup/deployment records and verified ownership tags. The Attestra adapter uses those sources. Discovery does not guarantee knowledge of an omitted backend or every orphan in an AWS account.

Validate the application, AWS account, project, backend, stack and provider identities before mutation. A bucket prefix or tag is discovery evidence, not sufficient permission to delete it. [Canonical ownership labels](resource-ownership.md) supplement adopted target identity and operator authorization. External resources, shared keys, account-wide OIDC providers and DNS zones remain outside scope unless independently adopted with explicit ownership evidence.

## 2. Authorization and execution

1. Authenticate the operator; verify the actual cloud identity and report scope. Resolve the complete intended target scope before requesting destructive confirmation. Credential-vault selection chooses a credential source, not a single environment to delete.
2. Display the application/repository, account, regions, projects/backends, shared targets and recovery candidates. Require typed scope confirmation. Independently confirm customer-managed KMS key exclusivity; using a key for state encryption does not prove it is exclusive.
3. Capture and persist safe resource identifiers before deletion. Preserve earlier inventories when refreshed state or deleted stacks no longer contain those resources. Record whether a complete target inventory was obtained, including a valid empty stack.
4. Attempt environment stacks before shared admin/index stacks. Continue independent targets after failures and retain their separate outcomes. Partial discovery or inventory failures stay visible and block a claim of complete cleanup.
5. Reconcile missing resources and remove managed deletion guards only within authorized stack ownership. Preserve encrypted secret envelopes when updating state guards. Never force-forget resources merely to make the report appear clean. Unfinished Pulumi operations or unsafe provider overrides make inventory uncertain and must be resolved before mutation.
6. Verify managed resources and attempt authorized residual cleanup. The application supplies exact DNS, repository environment, deployment-role and bootstrap-marker evidence when those artifacts live outside Pulumi. Do not remove deployment configuration while associated stacks remain or cannot be verified. Never delete the administrator session's own role.
7. Evaluate the separate recovery phase only after primary cleanup and report persistence succeed. Save results and verification evidence for later retries/checks.

Respect native stack locks. A stale-looking lock is not authorization to delete it. The Attestra implementation uses a local report lock, checks GitHub deployment activity before destructive phases, and uses conditional bootstrap leases for exact marker-history cleanup. Active/foreign locks and unknown marker contents are retained. These guards do not provide an account-wide distributed nuke lease across other checkouts or tools: deployments must remain suspended. A future hosted coordinator must enforce its own cross-operation exclusion.

Cancellation and crashes preserve evidence of completed effects; they cannot roll back deleted data. Report-save failure must stop further destructive work before inventory can be lost. Keep reports private, write them atomically and reject mismatched identities or corrupt/incompatible receipts rather than silently replacing them.

## 3. Verification and reporting

The report records scope, target identities, safe resource inventory, complete-inventory evidence, teardown results, latest check results and timestamps. It must include artifact type, physical identifier, environment/target, region and outcome. Never persist resource inputs, secret values, full state exports, credential material or raw provider error bodies. Custom drivers must also keep secrets out of identifiers and arbitrary metadata fields.

| Status | Meaning |
|---|---|
| `DELETED` | Verified present before cleanup and absent afterward |
| `ABSENT` | Authoritative read-back confirms absence; this is successful cleanup |
| `REMAINS` | The artifact still exists |
| `UNVERIFIED` | Access failure, incomplete response, unsupported type or missing inventory prevents a conclusion |
| `FAILED` | A recovery removal failed |
| `RETAINED` | Recovery cleanup was deliberately blocked |
| `SCHEDULED` | KMS deletion is pending; the key is not yet destroyed |

A successful delete request alone does not prove absence. Authentication/permission failures, missing response fields and unknown resource kinds must not become `ABSENT`. A missing stack without surviving complete inventory cannot certify that its cloud orphans were removed. Fresh empty discovery must not authorize deletion of the last recovery artifacts without primary inventory evidence.

The reference driver verifies supported AWS resources, including resources in legitimate cross-region providers. Unsupported resources remain unverifiable. Auxiliary inventory includes Lambda log groups and table-backup collections that survive stack removal. DynamoDB SYSTEM backups created upon table deletion and separately managed AWS Backup recovery points must remain visible; an empty DynamoDB backup listing alone does not prove all backup data is gone. Non-user backups require their service-specific cleanup or retention lifecycle.

Secrets Manager secrets and secret versions are verified through parent metadata, without retrieving secret values. Scheduled secret deletion is still present and blocks recovery cleanup until actual absence. Nuke does not silently override the secret's configured recovery window. KMS scheduling is likewise reported distinctly from destruction; subsequent checks treat a pending key as remaining.

## 4. Recovery state and key deletion

Recovery deletion is opt-in for explicitly adopted, exclusive state buckets and customer-managed keys. Application/shared resources must not be silently reclassified as recovery resources by an inventory adapter.

The required gate is:

- Every primary artifact has a successful, independently verified cleanup outcome. Remaining, failed, retained or unverifiable evidence blocks recovery.
- All recovery candidates pass preflight before recovery deletion begins. Verify bucket owner, adopted scope, remaining stacks and allowed object paths; retain unknown objects and foreign-project state.
- Application-owned readiness/pending-marker histories are handled by the application's narrowly scoped adapter. Do not broaden the generic state-object allowlist to bypass active locks or unexplained data.
- Process state buckets before keys. Every recovery bucket must be verified absent before scheduling any key deletion.
- Verify customer-managed key identity, independent exclusivity and multi-region eligibility. AWS-managed/shared keys are not implicitly removable. Report pending deletion separately and preserve any unresolved candidates.

A backend bucket or recovery key embedded in a normal target stack must not be destroyed during the environment phase; its ownership must be separated so the gate can control it. State-bucket encryption and the Pulumi secrets provider are different layers and can reference different keys. Record both when present; credentials/passphrases stay outside the report.

## 5. Full checks, fast checks and retries

| Operation | Input | Behavior |
|---|---|---|
| Nuke/retry | Current adopted scope plus saved inventory | Attempts cleanup and produces current per-artifact outcomes |
| Full check | Saved artifact inventory | Re-verifies all recorded artifacts without destruction or new environment discovery |
| Fast check | Latest check snapshot | Queries only artifacts last checked as `REMAINS` |

Fast check requires an earlier check; it never silently falls back to checking everything. Preserve skipped results and their individual timestamps. Skipped `ABSENT` artifacts are not queried again, and skipped `UNVERIFIED` evidence does not become overall success. If nothing remains in the latest check snapshot, make no artifact probes. A full check is needed to revisit unknowns or detect resources that reappeared after confirmed absence.

Checks can run after stacks disappear, including reports that contain only external artifacts. Resource-scoped lookup, such as resolving the zone for an exact saved DNS record after credentials become available, is part of verification; it must not expand the environment deletion scope. No check mode invokes cleanup, recovery deletion or key scheduling, and a passing check does not automatically authorize a later destructive recovery phase.

Retry nuke with its surviving inventory rather than discarding the report or treating recreated resources as earlier deletion evidence. A new nuke invalidates stale check snapshots. Record fresh checks separately from the original teardown results, with enough timestamps/scope information to distinguish cached evidence from current observations.

## 6. Go reference usage

From a checkout of `go.infra.composer`, supply an adopted [configuration](https://github.com/lambdawalker/go.infra.composer/blob/f95a74e819ca4e5ce151856a755dfd5c0f61581c/examples/teardown/nuke.example.json):

```sh
go run ./cmd/infra-nuke -config ./nuke.json -nuke
go run ./cmd/infra-nuke -config ./nuke.json -check
go run ./cmd/infra-nuke -config ./nuke.json -fast-check
```

The reusable Go entry points are `teardown.Engine.Nuke(ctx)` and `Engine.Check(ctx, fast)`. The driver supplies discovery, inventory, destruction, authoritative inspection and recovery removal; recovery also requires preflight support. An optional artifact cleaner handles residual resources after target destruction. Embedding callers provide authorization and coordination. See the [implementation guide](https://github.com/lambdawalker/go.infra.composer/blob/f95a74e819ca4e5ce151856a755dfd5c0f61581c/teardown/README.md).

From the Attestra application checkout:

```powershell
.\deploy.bat -teardown -nuke
.\deploy.bat -teardown -nuke -check
.\deploy.bat -teardown -nuke -fast-check
```

The corresponding Unix launcher is `./deploy.sh` with the same flags. The application bypasses its single-environment startup picker for these operations. Its report is `.attestra/nuke.<account>.local.json`; the generic CLI defaults to `.infra-composer/nuke.<application>.<account>.json` beside its configuration. The schemas are implementation-versioned; legacy auth receipts are not imported automatically. Credential vaults and local setup records are retained by the current Attestra nuke integration. See the [application guide](https://github.com/lambdawalker/go.attestra.aws/blob/48f034ef06440e3e28fa44e81314621fa5cf778f/tools/deploy/README.md#all-environment-nuke).

## 7. Acceptance criteria

- All adopted environments are attempted before shared admin/index; independent failures do not erase successful progress.
- Foreign account/project identities, unsafe provider credentials, incomplete exports and pending Pulumi operations cannot authorize deletion.
- Complete inventories are saved before mutation and survive missing stacks; an uncertain/partial inventory never masquerades as complete evidence.
- Confirmed absence succeeds; denial, malformed responses and unsupported resource types remain distinguishable from absence.
- Application-specific cleanup verifies exact ownership and fails safely on active locks, caller-owned roles, changed DNS targets or inaccessible repository metadata.
- Backups, pending secret deletion and residual logs remain in scope after their stack disappears.
- Any primary uncertainty or failed report write preserves recovery state; all buckets are absent before key scheduling starts.
- Full/fast checks make no destructive calls; fast selection uses the latest check result and preserves skipped unknowns/timestamps.
- Tests use fake provider/process runners and local files for failure, cancellation, recovery ordering, retry and read-only behavior. Live teardown is never a documentation validation step.

Hosted authorization capabilities, cross-checkout distributed leases and a durable admin-job UI remain follow-on design work. They must not be represented as already provided by the CLI reference.
