# DNS: post-deployment configuration and custom-panel plan

## 1. Scope and current provider boundaries

Reviewed Attestra commit [4607807](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/api_domain.go) on 2026-11-01. This is a proposed panel/adapter design, with no DNS mutation. Follow the [configuration policy](../configuration-and-administration.md).

| Resource | Current behavior |
|---|---|
| API/index/admin hostnames | Optional Route53 integration; CNAME to regional API Gateway, TTL 300 |
| ACM validation | Optional Route53 CNAME records, TTL 300; otherwise external publication |
| SES verification/DKIM | Route53 TXT/CNAME records when zone configured |
| Android association host | Optional Route53 A alias to CloudFront |
| Cloudflare setup helper | SES TXT/CNAME only, DNS-only, new records TTL 300 |

Sources: [API](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/api_domain.go), [shared index](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/main.go), [admin](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go), [associations](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/assetlinks.go), [SES](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [Cloudflare adapter](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/dns/cloudflare.go), [bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/bootstrap.go). The Cloudflare helper is not a general hostname or ACM editor. External-provider DNS remains a distinct ownership boundary.

## 2. Two dashboard sections

### Application settings

Show approved logical service URLs, sender identity and association intent in the relevant application view. Their underlying DNS bindings belong in Artifact settings. App URL edits may have high security impact even though they are application properties. A sender wording editor cannot change domain ownership or redirect traffic.

### Artifact settings

Show provider, account/zone, authoritative zone name, environment/shared scope, logical purpose, record name/type/value, proxy/alias state, managed revision and drift. Distinguish desired records from observed provider state and public resolver observations. Classification and risk are separate: inspection is low-impact artifact access; traffic redirection is privileged artifact access.

## 3. Useful bounded controls

| Control | Proposed exposure |
|---|---|
| Inspect validation/delivery records and propagation | First read-only increment |
| Reconcile missing owned SES/ACM record | Narrow provider adapter, reviewed exact diff |
| TTL for eligible non-alias owned records | Bounded advanced setting; show old-cache window |
| Switch an owned hostname to approved replacement | Migration job with TLS/readiness checks |
| Proxy status | Locked DNS-only for validation/DKIM; no generic toggle |
| Zone delegation, registrar, DNSSEC, arbitrary records | Deployment/specialist workflow, outside initial panel |

Preserve unrelated TXT values and records. Current Cloudflare planning retains matching TXT entries, refuses conflicting CNAME/NS cases, and only unproxies a matching CNAME. Deletion checks both exact content and approved record ID. A future adapter should retain these protections and record ownership provenance; equality of value alone does not prove exclusive ownership.

## 4. Prerequisites and type constraints

Verify authoritative delegation, selected zone containment, provider access and service validation requirements before writes. Route53 aliases and ordinary CNAMEs are different types: standard CNAMEs cannot occupy a zone apex; Route53 aliases can target eligible AWS resources there. Current API/index/admin CNAME generation therefore requires non-apex hostnames, or a deliberately implemented alias migration. Cloudflare apex CNAME flattening is provider-specific and does not make Route53 CNAME behavior equivalent. Do not flatten ACM validation CNAMEs indiscriminately; validate provider resolution behavior.

TTL changes do not purge already cached answers or provide instantaneous global revocation. Allow for previous TTLs, negative caches and resolver behavior. Provider API success means control-plane acceptance; separately check authoritative answers, recursive observations and actual TLS/service availability.

Changing a hostname affects CORS, OAuth callback/logout URLs, passkey RP IDs, bootstrap documents and clients. A DNS write does not migrate existing passkey credentials or authorize a new origin. Shared administrator/index endpoints require independent operator access during migration.

## 5. Binding, authorization and jobs

Declare dns.record.inspect, dns.record.reconcile and dns.hostname.migrate as typed artifact capabilities, each with sensitivity/risk and provider-bound permission. These are illustrative names. The app-owned custom panel suppresses any standalone feature panel; both use the same validated backend.

Resolve the target from a trusted registry containing zone ID, exact name/type, purpose, provider credential reference and owner. Reject browser-supplied arbitrary zones/records. Use separate read-only and write workers. Route53 writers receive selected-zone permissions and condition restrictions on record names/types/actions where supported. Cloudflare uses zone-scoped API tokens with only needed Zone Read/DNS Edit capabilities, stored through a protected vault/secret provider; never return tokens to the browser, previews or logs. Current deployment credential-vault use is not a completed hosted panel secret service.

A durable job validates expected revision, leases the record set, reads current state, compares approved fingerprints, previews preserved values, applies, waits and reads back. Recheck immediately before mutation; external changes trigger conflict rather than overwrite. APIs/providers differ in transactional guarantees, so record partial completion and make retries idempotent. Do not label a multi-provider change atomic.

## 6. Ownership, recovery and rollout

Pulumi remains authoritative for current Route53 records; bootstrap owns the selected external workflow. Establish one writer per record and an explicit import/handoff before runtime edits. Later deployments must consume the updated desired registry. Avoid broad ignoreChanges or deleting another consumer's shared verification record.

Keep old endpoint resources and exact before-values for a recovery window. Rollback validates current ownership and service health before restoring records; caches may continue serving both answers. Do not delete validation records still needed for ACM renewal or SES. Removing DNS is not immediate credential/session revocation.

Phase delivery as inspection, then owned validation-record reconciliation, then bounded TTL/hostname migrations. Tests cover apex/type constraints, zone escape, token redaction, TXT preservation, record-ID replacement, proxy refusal, stale revisions, partial provider failure, ownership conflicts, negative caching and migration dependencies. Follow mock tests with controlled authoritative DNS and HTTPS checks. This document implements no panel or DNS changes.

## 7. Provider references

- [Route53 alias versus CNAME](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html)
- [Cloudflare token creation/scoping](https://developers.cloudflare.com/fundamentals/api/how-to/create-via-api/)
- [Cloudflare TTL behavior](https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/)
- [Cloudflare CNAME flattening](https://developers.cloudflare.com/dns/cname-flattening/)
- [ACM validation records](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)
