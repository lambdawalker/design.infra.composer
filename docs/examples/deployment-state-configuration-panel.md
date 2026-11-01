# Deployment tooling and state: configuration and custom-panel plan

## 1. Scope and source baseline

Covers the operator/deployment artifact, its encrypted memory, Pulumi backend and CI integration. Follow [configuration policy](../configuration-and-administration.md); source [4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e), reviewed 2026-11-01.

The [Go wizard](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/bootstrap.go) provisions/checks private versioned S3 state, verifies owner/region, and preserves existing encryption. The [stack bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/bootstrap_stack.go) selects/initializes deliberately, requires the existing passphrase provider, and guards against silent proof-key regeneration. Do not claim a customer-managed KMS key is created by this code.

The [credential vault](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/vault/credential_vault.go) uses Argon2id-derived keys and AES-GCM with repo/environment scope. It stores operator credential material separately from application runtime data. SSO/temporary credentials and GitHub environment-bound OIDC are distinct from Cognito app/admin login.

Proposal only. This plan does not unlock/export a vault, change GitHub secrets, deploy, cancel a lock or migrate state.

## 2. Useful settings and their location

| Section | Property | Exposure |
|---|---|---|
| Application settings | Declared feature defaults/behavior used to seed a new environment | Existing typed contract, no resetting an administrator override |
| Artifact settings / Deployment | Selected application/environment and backend/shared scope | Routine operator selection with full target summary |
| Artifact settings / Deployment | Account/region/profile or role reference | Read-only once adopted for a deployment identity; change through explicit rebind/migration checks |
| Artifact settings / Deployment | DNS provider/zone and CI repository/environment bindings | Privileged target-bound change, coordinated with DNS/IAM plans |
| Artifact settings / Deployment | Permitted build parallelism, freshness/reuse options and operation timeouts | Bounded future controls only if tool exposes them; hashes do not prove cloud drift is absent |
| Artifact settings / Deployment | Default operation/preview and allowed promotion targets | Typed workflow policy, separate from permission to execute it |
| Artifact settings / Credential memory | Credential presence/provider, expiry and masked replacement | Local authorized operator or supported secret-service backend; never reveal existing values |
| Artifact settings / State | Backend/stack identity, encryption provider, backup/versioning health | Inspect first; changes use migration/recovery workflow, not an ordinary Save |

Do not make teardown, reset, state import, force unlock, production promotion, credential export or backend replacement side effects of a settings save. They are separately authorized operations with exact targets and audit.

The application/admin panel cannot read a developer's local vault merely because it controls the deployed application. Local memory settings require a local CLI/agent interface or a separately designed authenticated operator channel. Hosted workers use their own scoped credentials/secret references.

## 3. Custom-panel flow

Show application, account, region, environment, backend/project/stack, scope, role/credential provider status, last successful code/configuration hashes, active job/lock and desired/applied/observed revision. Distinguish local saved preference from shared deployment authority and actual cloud state.

Routine actions: inspect → choose approved target/operation → resolve settings/secret references → preview concrete changes → submit durable job → observe checkpoints/read-back. A saved preference does not execute a deployment.

Credential replacement uses a protected write-only input, source-specific validation and masked status. Prefer temporary federated/workload credentials where supported; never collect an AWS sign-in password as the default mechanism. A failed provider request must distinguish expired/denied credentials, networking, throttling and missing resource rather than asking for every secret again.

## 4. State and credential changes need dedicated plans

**Vault unlock/passphrase:** unlocking does not rotate cloud credentials or re-encrypt Pulumi state. Vault passphrase rotation, Pulumi secrets-provider/passphrase changes, and S3 encryption-key changes are different operations. Version/backup/recovery procedures must be explicit; never keep the unlocking key beside ciphertext.

**Backend/stack migration:** verify original owner/account/region, capture protected backups and resource identities, stop competing operations, follow a supported state migration procedure, prove the destination can decrypt/read state, and verify no resource duplication/recreation before making it authoritative. State contains sensitive metadata even when marked secrets are encrypted.

**Encryption:** preserve existing access and key availability until verification/rollback windows pass. S3 at-rest encryption and Pulumi secret encryption protect different layers. Do not infer that changing the bucket encryption automatically migrates existing objects or Pulumi secret providers.

**Locks:** respect Pulumi's native per-stack locks/history and the application's cross-operation coordinator. A stale-looking lock is not proof no worker is running. Detect job ownership/liveness; recovery/cancel is an explicit operator action, never automatic file deletion on retry.

**CI:** use a trusted workload role/OIDC with exact repository/environment constraints and appropriate environment protections. A local vault is not copied to GitHub as a single broad secret. Reconcile approved CI secret/variable references deliberately; prevent revealing tokens or weakening role trust as a convenience.

## 5. Authority and permissions

The operator panel submits jobs to a worker; it never becomes a shell/command textbox or browser AWS credential distributor. Use allowlisted operation parameters and trusted target manifests, not arbitrary repo URLs, paths, commands, role ARNs or backend URLs.

Separate local operator rights, environment deployment rights, shared-stack rights, state/security recovery, and CI/DNS administration. A runtime settings editor receives none automatically. Refer to [IAM/OIDC](iam-oidc-configuration-panel.md), [DNS](dns-configuration-panel.md) and [S3](s3-configuration-panel.md).

Maintain one registry of adopted mutable configuration. CLI, admin and CI use the same resolver/coordinator and consume current managed overrides. Rebuild/repreview on relevant source/config/target changes; reuse unchanged artifacts only when verified hashes and context permit it. A code hash match does not authorize skipping IAM/configuration/state checks.

Write vault updates atomically with restricted access; serialize concurrent changes. Persist shared job progress/revisions outside one developer's local preferences. Redact subprocess output, preview/state exports, exceptions and URLs; do not pass raw credentials through shell history or query strings.

## 6. Failure, recovery and delivery

Record checkpoints before irreversible transitions. A failed backend/secret migration must retain the original authoritative path and recovery evidence; no success marker until read-back/decryption/resource identity checks complete. Rollback must not restore an obsolete vault/cloud token or overwrite another operator's new revision.

Deliver in stages: read-only target/credential/state inspection; bounded routine defaults and job submission; source-specific credential replacement; independently reviewed vault/state/CI migration workflows. Keep destructive recovery out of the initial panel.

Test repo/environment vault isolation, invalid/expired credentials, no secret output, concurrent vault writes, wrong account/region/backend, missing original state, failed decryption, stale/active locks, interrupted migration, CI subject mismatch, shared-resource permissions, override preservation, partial deployment resume and noninteractive worker operation. Do not validate this plan by deploying or exporting real secrets.

## Provider references

- [AWS IAM temporary credentials and least privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [GitHub OIDC with AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [Pulumi DIY state backend/locking](https://www.pulumi.com/docs/iac/operations/stack-management/using-a-diy-backend/)
- [Pulumi secrets providers](https://www.pulumi.com/docs/iac/concepts/secrets/)
