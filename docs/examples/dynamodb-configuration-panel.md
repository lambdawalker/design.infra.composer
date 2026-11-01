# Attestra DynamoDB configuration panel plan

## 1. Status and source baseline

Proposed adapter and custom-panel capability only; no implementation or cloud change. Source reviewed at [Attestra commit 4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e), with AWS guidance checked on 2026-11-01. Follow [configuration policy](../configuration-and-administration.md) and [artifact inventory](attestra-configuration-plan.md).

| Logical table | Current source-derived configuration |
|---|---|
| Environment email proofs | PAY_PER_REQUEST; string `id` key; numeric `ttl` expiry attribute enabled; PITR and server-side encryption enabled |
| Environment ID captures | Same billing/protection baseline; string `id`; `work-due` GSI with string `work`, numeric `due`, ALL projection; `ttl` enabled |
| Environment reset control | PAY_PER_REQUEST; string `id`; PITR/encryption enabled; no TTL declaration |
| Shared environment registry | PAY_PER_REQUEST; string `id`; PITR/encryption; Pulumi protection |
| Shared admin runtime | PAY_PER_REQUEST; string `id` plus string `sk`; PITR/encryption; native deletion protection and Pulumi protection |

Evidence: [environment resources](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [capture resources](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [reset control](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/reset.go), [registry](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/main.go), [admin runtime](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go). Omitted settings require native inspection; do not infer deletion protection on every table or a particular customer-managed key.

## 2. Application settings versus Artifact settings

**Application settings** include proof acceptance lifetime, capture admission/consent policy and evidence-retention behavior. Lifetimes affect authorization and privacy even when stored in a database; they require their own security-sensitive permissions. Capture retention is currently fixed at seven days, and capture metadata is initially assigned a 90-day TTL. Neither is presently an arbitrary editable runtime retention field.

**Artifact settings** include table billing, capacity limits, PITR, encryption, deletion protection, TTL mechanism and bindings/IAM. Database contents do not become artifact settings merely because DynamoDB stores them. Source: [runtime model](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/model.go) and [capture service](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/capture/service.go).

Expiry must be enforced by application timestamps and conditional operations. [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html) removes items asynchronously, typically days later; expired items can remain readable. A TTL toggle cannot extend a proof's validity, revoke access immediately, or guarantee deletion at a precise deadline.

## 3. Curated property contract

| Typed property | Operational value and proposed exposure |
|---|---|
| `recovery.enabled: boolean` | Read-only baseline initially; later privileged enablement, with disabling treated as loss of recovery coverage |
| `recovery.period_days: integer[1,35]` | Later bounded PITR window control; show effective restorable timestamps and cost assumptions |
| `deletion_protection.enabled: boolean` | First bounded write: enable protection; disabling requires a separate destructive-operation capability |
| `billing.mode: enum` | Inspect first; later coordinated capacity plan, never an isolated dropdown |
| `capacity.max_read/max_write: integer` | Later on-demand limits with throttling impact and GSI coupling checks |
| `ttl.attribute/status`, key/GSI definitions, encryption reference | Read-only diagnostics; migration-controlled changes |

Declare category, sensitivity, units, permission and impact independently. A proposed `ManagedResourceProperty(adapter="aws.dynamodb.table", property="deletion_protection.enabled")` resolves a trusted table binding; this is illustrative, not an existing API. AppConfig cannot apply table settings. Use native `DescribeTable`, `DescribeContinuousBackups`, `DescribeTimeToLive`, `UpdateTable` and `UpdateContinuousBackups` through approved adapters.

## 4. Transactional state is not cached configuration

[Runtime store](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/store.go) uses consistent reads and transactions coupling active grant revisions, current configuration and history. Bootstrap reconciliation also checks registry revision/lock ownership. [Capture worker](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/capture/worker.go) uses record revisions, generations and leases to reject stale publication.

Keep grants/revocations, leases, reset fences, idempotency records and operational state authoritative in their transactional store. Do not migrate them into stale AppConfig snapshots. Delivery of eligible application policy through another reader requires explicit freshness semantics and preservation of authorization checks at write time.

## 5. Custom-panel and native job flow

1. Inspect account/region, application/environment or shared boundary, logical table, effective state, owner, desired/applied revision and drift.
2. Select an approved property; preview table/GSI consumers, retained releases, protection loss and recovery impact.
3. Authorize environment/property/action and expected revision server-side; resolve physical identifiers from deployment bindings.
4. Persist an idempotent job and acquire a per-table coordinator lease. Read native state and compare its normalized fingerprint with preview.
5. Apply only supported updates, wait for native completion, and verify effective state before advancing the applied revision.
6. Record partial failure, retryable steps and observed state durably; resume by inspection rather than blindly repeating writes.

[UpdateTable](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateTable.html) is asynchronous and has concurrency restrictions. Coordinator revisions do not prevent external AWS writers racing; recheck drift between steps. Do not overwrite unrelated native fields or claim success merely from request acceptance.

## 6. Ownership, migration and recovery

Pulumi owns current declarations. Establish field ownership and a shared desired-state registry before enabling panel writes, so later deployments preserve approved values. Do not ignore the entire resource. Keep bootstrap/shared-stack ownership separate from environment operators.

Primary-key changes, table replacement, GSI removal, TTL attribute migration and encryption-key changes need explicit migration plans. Preserve dispatcher access to `work-due`; backfill/read compatibility and IAM changes precede cutover. Reset/table clearing is a separately authorized data operation, never a settings-save side effect.

[PITR restore creates a new table](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/pointintimerecovery_restores.html). Recovery must restore required TTL/protection/PITR, policies and bindings, reconcile writes after the chosen point, validate consumers, and deliberately adopt/cut over the replacement in Pulumi. Restoring grants or reset state can resurrect revoked authority or obsolete locks; inspect and reconcile those records before serving traffic. Recovery cannot recreate S3 evidence already permanently deleted.

## 7. Permissions and delivery checks

Use separate `application.settings.write`, environment `storage.table.configure`, shared-table, recovery and destructive-data capabilities. The worker receives only required describe/update actions on registered tables; runtime roles retain item/prefix-scoped data access. Browser sessions receive no AWS credentials, item dump or arbitrary table ARN control.

Phase one delivers inspection/drift; phase two protection enablement and recovery controls; phase three capacity/migration workflows. Tests cover category/permission isolation, shared-target rejection, TTL versus logical expiry, transaction/grant fences, stale revisions, external drift, asynchronous/partial failure, Pulumi preservation, restore binding changes and protection against resurrected grants. No live restore/reset is implied.

## 8. Additional provider reference

- [PITR management and recovery period](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateContinuousBackups.html)
- [Expired items remain accessible before TTL removal](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ttl-expired-items.html)
