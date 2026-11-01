# Attestra S3 configuration panel plan

## 1. Status and current boundaries

Proposed adapter/custom-panel capability only, based on [Attestra commit 4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e). AWS guidance checked on 2026-11-01. No bucket, object, deployment or credential is changed. Follow [configuration policy](../configuration-and-administration.md) and [artifact inventory](attestra-configuration-plan.md).

| Bucket purpose | Source-derived baseline and owner |
|---|---|
| Environment ID evidence | Pulumi; forceDestroy false; versioning enabled; BucketOwnerEnforced; all public-access blocks; AES256 default encryption; deny non-TLS access |
| Shared Pulumi state backend | Setup wizard creates/reuses owned regional bucket; ensures versioning/public blocking and preserves existing encryption; separate backend prefix access |
| Application association documents | Pulumi; forceDestroy false; BucketOwnerEnforced; public blocking; AES256; private origin accessed through CloudFront origin access control |

Evidence: [capture infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [state bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/bootstrap.go), [backend IAM](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/aws_setup_policy.go), [association hosting](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/assetlinks.go). Do not apply evidence lifecycle defaults to state or association buckets. Omitted association versioning/lifecycle declarations are not proof of effective native state.

## 2. Application settings versus Artifact settings

**Application settings** contain evidence-consent wording, capture admission and logical evidence-retention policy. These remain application behavior regardless of source. Retention is privacy-sensitive, independently of its dashboard category. Current [runtime policy](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/model.go) and [capture bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/awscapture/bootstrap.go) fix retention at seven days; the existing runtime schema does not expose a general retention edit.

**Artifact settings** cover lifecycle rules, versioning, encryption/KMS bindings, access policy and bucket bindings. Association identity declarations need their own application/deployment validation because they authorize app links; they are not an arbitrary object editor. State bucket access and backend relocation belong to a separate shared operational boundary.

## 3. Retention has several clocks

The evidence lifecycle applies across the bucket: current-version expiration after ten days, noncurrent-version expiration ten days after becoming noncurrent, and incomplete multipart abort after one day. This orphan safety net differs from the worker's seven-day logical retention and version-specific cleanup. Evidence: [worker](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/capture/worker.go) and [finalization/version pinning](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/capture/service.go).

[S3 lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html) acts on existing eligible objects too. Shortening a rule can schedule old evidence immediately. In a versioned bucket, current expiration usually creates a delete marker; noncurrent expiration permanently removes versions. Ten plus ten is not a single guaranteed physical retention duration, and logical expiry is not proof that all versions were erased.

Keep versioning enabled: finalization rejects missing/null version IDs and processing reads pinned versions. Suspending it can break evidence integrity. [Versioning cannot return to an unversioned state](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html). Object Lock, replication, legal retention and backup integration require separate compatibility work with deletion obligations.

## 4. Curated typed properties

| Property | Useful exposure after deployment |
|---|---|
| `evidence.orphan_expiry_days: integer` | Advanced bounded lifecycle control; require retention/processing-window compatibility and existing-object impact preview |
| `evidence.noncurrent_expiry_days: integer` | Separate permanent-deletion boundary; show version/cost/privacy impact |
| `multipart.abort_days: positive integer` | Later bounded operational control, preserving legitimate upload windows |
| `encryption.algorithm: enum`, `kms_key: protected reference` | Inspect initially; planned migration with producer/consumer/KMS access checks |
| Versioning, ownership, public blocking, TLS policy | Read-only security/integrity invariants initially |
| State backend and association origin bindings | Read-only links to dedicated deployment workflows |

Use a proposed `ManagedResourceProperty(adapter="aws.s3.bucket", property="evidence.orphan_expiry_days", units="days")` with category, permission and risk metadata. Native operations include lifecycle/encryption/versioning inspection and approved `PutBucketLifecycleConfiguration`/`PutBucketEncryption` calls. AppConfig does not manage buckets.

## 5. Custom-panel workflow and adapter

1. Inspect registered account/region, environment/shared scope, purpose, logical/physical target, revision, ownership and drift; omit object contents and signed URLs.
2. Select a curated property and preview affected prefixes, current/noncurrent versions, processing deadlines, costs and irreversible outcomes.
3. Authorize property/action/target, expected revision and observed fingerprint; persist an idempotent job and acquire a bucket-scoped lease.
4. Read current native configuration; preserve unrelated rules/settings, reject unsupported fields, then apply the smallest supported operation.
5. Read back each subresource, record step results and verify approved data-plane access with controlled fixtures only.
6. Mark applied revision after verification; expose partial failure and a resumable recovery plan.

[PutBucketLifecycleConfiguration replaces the configuration](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutBucketLifecycleConfiguration.html), so a one-rule form must not drop other rules. Internal leases/fingerprints do not provide AWS-wide compare-and-swap; detect external drift and stop conflicting jobs.

## 6. Encryption, IAM and ownership

[Changing default encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html) does not reencrypt existing objects. Explicit upload encryption can override the default. A KMS migration must inventory versions, examine transport headers, update key/resource/identity policies and CloudFront compatibility, retain old-key decryption access, and verify actual writes/reads. Rewriting existing objects is a separate version-aware data job with cost and metadata implications.

Separate environment evidence operators, shared backend operators and association deployment operators. Give the configuration worker only required bucket-subresource actions on registered targets, with expected-owner checks where supported. Evidence runtimes retain prefix/version-scoped object permissions; configuration editors receive no evidence-download/delete permission automatically. KMS grants and access policies are separate privileged capabilities. The browser receives no AWS credentials or backend secrets.

Pulumi owns evidence/association declarations; the wizard owns backend preparation. Define field-specific handoff and registry reconciliation before panel writes. Subsequent deployments/setup must preserve accepted managed values. Do not solve ownership conflicts by blanket ignoring all bucket settings.

## 7. Destruction, recovery and delivery

Bucket replacement/region move, public access, arbitrary policies, backend migration, version deletion and reset remain explicit operations. Deleting a version or lifecycle-expired data has no trivial rollback: restoring the old lifecycle cannot resurrect it. Partial encryption/policy changes can strand readers; retain before-state references and restore access through a new validated job. Cancelling a data job does not reverse completed deletes or copies.

Phase one inspects all three boundaries; phase two adds validated evidence lifecycle controls; phase three adds encryption migrations and dedicated backend recovery. Tests cover full-rule preservation, existing-object impact, version pins, seven-versus-ten-day clocks, permission isolation, shared-target rejection, drift/revision conflicts, KMS/reader partial failure, resumable jobs and Pulumi reconciliation. No production-object deletion or backend relocation is part of these tests.

## 8. Additional provider reference

- [Lifecycle expiry and permanent-deletion recovery limits](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-lifecycle.html)
