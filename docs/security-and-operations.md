# Security and operational baseline

## Status and trust boundaries

**Recommended baseline, 2026-11-01; not implemented by this document.** Applies to generated panels, custom panels, CLI/CI and workers. It refines [configuration and administration](configuration-and-administration.md), retaining security → applicable provider guidance → cost.

| Boundary / threat | Required design response |
|---|---|
| Feature package → deployment process | Locked provenance; trusted declaration code; restricted worker identity; no claim Python imports are sandboxed |
| Browser → configuration API | Authenticated requests, per-target authorization, validated property schemas and protected sessions |
| API/job queue → privileged worker | Server-derived target bindings, bounded operations, execution-time authorization and idempotency |
| Worker → AWS/provider | Separate read/write roles, least privilege, effective-access checks and native conflict protection |
| Vault/state/configuration → logs/discovery | Secret-aware values, allowlisted serialization and explicit public projections |
| Shared state → deployment/recovery | Independent recovery, native locks, revision checks and protected audit evidence |

A compromised deployment worker can use its granted privileges; encryption does not make that process harmless. Separate application runtime, configuration-worker and foundation/operator permissions. Break-glass access must work independently of the authentication feature being changed.

## 1. Secret custody and information flow

| Secret class | Custody / access direction |
|---|---|
| Local operator credentials | Authenticated encrypted vault; unlock through OS credential manager or operator passphrase/KDF; no key beside ciphertext |
| CI/hosted worker identity | Prefer short-lived federation/workload credentials; protected service source where a static secret is unavoidable |
| Application runtime secret | Provider secret service with scoped reader, rotation and declared cache freshness |
| Pulumi secret-bearing values/state | Secret-aware Outputs/configuration and selected stack secrets provider; protected backend and decryption access |
| Recovery material | Independently protected backup and documented restore/decryption authority |

The exact vault backend, KDF parameters and shared secrets provider remain open until implementation review. Do not imply KMS, SSO or secret caching is already provisioned by the prototype. Losing the only passphrase/key can make recovery impossible.

Mark sensitivity at declaration and propagate it through references, transformations, adapter inputs and outputs. Default serializers expose safe metadata/references rather than values. Resource names, IDs, URLs and error messages must never embed secrets; not every provider metadata field can be secret-marked. Validate secret-bearing defaults and reject sources that cannot preserve protection.

In a future Pulumi adapter use secret configuration/Outputs and explicitly mark sensitive computed outputs where provider inference is insufficient. Secret callbacks can still receive plaintext: no printing, generic JSON encoding, exception interpolation or writing temporary plaintext there. Secret marking protects tracked persistence, not arbitrary application logging. Audit subprocess output, previews, provider diagnostics and state-export paths; disable unrestricted secret-display/debug options in hosted jobs.

Prefer references over copying runtime secret values into function environments or public manifests. Do not hash low-entropy secrets into public diffs; hashes may permit guessing. Record protected version IDs/change references instead. A reference itself can be sensitive metadata.

## 2. Rotation and recovery

A rotation job identifies the secret owner, reader population, allowed overlap and freshness bound. Create the replacement, validate scoped access, stage compatible consumers, verify effective use, revoke the old material, then expire caches within the declared bound. Persist partial states and never announce rotation complete solely because a secret-store write succeeded.

Some providers cannot overlap credentials. Their adapter must declare the outage/recovery sequence rather than applying this sequence blindly. Emergency compromise response may revoke first, accepting disruption. Restoring an old configuration is not permission to reactivate a compromised credential.

Vault unlock rotation, cloud credential rotation, Pulumi secrets-provider migration and bucket-encryption changes are different jobs. Keep recovery access/old decryption keys until approved verification windows finish. Recovery tests use synthetic fixtures; no secrets in Git or support bundles.

## 3. Authorization contract

Authorize a subject against an action and scope tuple: application, environment or explicit shared scope, feature instance, artifact, property and release where relevant. Default deny; missing scope is not a wildcard. Backend-declared category/risk/permissions cannot be overridden by request fields.

Suggested role bundles are conveniences, not an implicit hierarchy:

| Bundle | Allowed scope |
|---|---|
| Viewer | Authorized metadata/status, not secret values or all log contents |
| Application editor | Approved logical properties; separate permission for sensitive policies |
| Artifact operator | Curated resource settings for registered targets |
| Deployment operator | Approved deploy/promotion operations |
| Security/recovery operator | Explicit identity, key, state and recovery capabilities |

Grants must be bounded by the grantor's delegation authority. No self-escalation, worker self-policy mutation or automatic inheritance from application editor to deployment operator. Destructive/shared/identity operations get separate capabilities; production policy can require step-up authentication or independent approval.

Humans use the selected admin identity provider; CI workers use their separately bound workload identity. Neither an asserted client version nor an application-admin JWT automatically grants AWS access. Identity-provider selection remains open for the general framework; the Attestra example's Cognito choice is not mandatory.

Authorize job submission, execution and privileged resume/checkpoints. Recheck grant revocation and policy revision; jobs do not carry a timeless authorization snapshot. A revoked user stops future privileged steps according to documented policy; completed native effects remain recorded. Background reconciliation uses its own explicit service authority, not an expired user's token. Avoid persisting bearer tokens in jobs.

## 4. Panel/API baseline

Use HTTPS, strict issuer/audience/token-purpose validation, bounded session lifetime and protected refresh/revocation. Internet-facing privileged operations require an appropriate strong-authentication policy. Scope job/status/history reads as carefully as writes.

Cookie sessions require Secure/HttpOnly/SameSite settings as applicable, CSRF defenses and exact Origin checks for state-changing requests. SameSite or CORS alone is insufficient. Bearer-token designs still need safe token handling, XSS protection and origin policy; do not prescribe one session architecture for every application.

Validate bodies against server-owned schemas: types, ranges, unknown fields, lengths, content types, approved destinations and immutable target bindings. Apply request/body/rate/job-concurrency limits and replay/idempotency rules. No state-changing GET requests, arbitrary AWS JSON, shell input or raw environment editors.

Escape rendered content, constrain help/update URLs, use CSP and safe dependencies, and prevent framing where inappropriate. Return safe errors with correlation IDs; detailed diagnostics remain in authorized redacted records. Secret replacement is write-only. Public discovery is an explicit allowlist, never serialization of the private artifact registry.

## 5. Durable execution, audit and tamper evidence

Before each privileged effect persist intent with actor/service identity, authorization/policy revision, target, expected configuration revision, operation ID and safe diff/reference. Record native result, verification and partial failure afterward. An accepted request is not an applied configuration.

Audit evidence should be append-oriented and copied to a separately controlled sink with retention and restricted deletion. Monitor delivery gaps and sequence continuity. Hash chaining alone is insufficient: an attacker able to rewrite the entire chain can recompute it. Signed checkpoints or external anchors need keys/access outside the writer's control; retention protection and operational gap detection remain necessary. Do not claim absolute tamper-proofing against account-wide compromise.

Choose and test audit-outage behavior. Initial privileged mutations fail closed when durable intent cannot be recorded. If an external effect completes before result logging fails, preserve pending status and reconcile native state without blindly repeating the effect. Emergency recovery uses a separately documented audited route.

Application settings still need concurrency checks and compatible-consumer validation. Artifact updates preserve unrelated fields and use native revision/ETag protection where supported. Internal leases cannot exclude external writers. Restore/rollback is another authorized conflict-checked job; it cannot reverse sent email, deleted evidence or exposed credentials.

## References

Primary guidance checked 2026-11-01; these are design requirements, not a security certification:

- [Pulumi secret tracking and callback plaintext](https://www.pulumi.com/docs/iac/concepts/secrets/)
- [Pulumi additional secret outputs and identifier limits](https://www.pulumi.com/docs/iac/concepts/resources/options/additionalsecretoutputs/)
- [OWASP REST security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
- [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP logging protection and verification](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
