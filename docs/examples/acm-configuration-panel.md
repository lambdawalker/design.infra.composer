# ACM: post-deployment configuration and custom-panel plan

## 1. Scope and current resources

Reviewed Attestra commit [4607807](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/api_domain.go) on 2026-11-01. This is a proposed panel and adapter design; it changes no deployed resources. Apply the [configuration policy](../configuration-and-administration.md) and [artifact inventory](attestra-configuration-plan.md).

| Certificate | Current source-derived behavior |
|---|---|
| Environment API | Optional apiDomain; DNS-validated ACM certificate in stack region, attached to REGIONAL API Gateway with TLS_1_2 |
| Shared index/admin | Separate DNS-validated regional certificates and API Gateway custom domains |
| Android association host | Optional assetlinks CloudFront distribution; separate ACM provider in us-east-1 |

Sources: [API domain](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/api_domain.go), [index](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/main.go), [administrator](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go), [association infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/assetlinks.go). Route53 records are conditional on route53ZoneId; otherwise DNS validation requires an external operator/provider. Issuance wait is already part of provisioning. A certificate ARN export is an identifier, not a private key.

## 2. Two dashboard sections

### Application settings

Show links to approved application URLs and authentication behavior. Editing displayed wording is an app property; changing the actual origin or relying-party domain is a coordinated migration. An application editor receives no certificate-management permission simply because the app consumes HTTPS.

### Artifact settings

Show trusted account, region, environment/shared boundary, logical certificate, ARN, covered names, status, expiry, renewal eligibility, validation records, attached resources, owner and observed revision. Mark shared-admin impact explicitly. Category and risk are independent: read-only expiry inspection is artifact configuration with low impact; an app-origin change remains security-sensitive application configuration.

## 3. Curated capabilities

| Property/operation | Proposed exposure |
|---|---|
| Expiration, validation and renewal health | First read-only increment, with failed/pending status |
| Approved operational tags | Later bounded edit; preserve ownership/security tags |
| Recheck pending validation | Authorized diagnostic job; no repeated certificate requests |
| Replace certificate for same approved names | Migration workflow with compatibility preview |
| Add names/change domain/region | Deployment-controlled migration, not scalar form save |
| Export/import key, disable validation, delete active certificate | No routine control |

Keep regional API Gateway certificates in the consumer's AWS region. CloudFront viewer certificates require us-east-1. Verify SAN coverage and service compatibility before association. The panel must never fetch, export, display or log private keys; imported certificates and external key custody are outside this initial capability.

## 4. Contract, readers and writers

Declare typed properties such as certificate.health (read-only) and certificate.replace (migration), with category=artifact, sensitivity metadata, risk, target scope and required permission. These names are pseudocode. The application owns its custom panel by default, suppressing the optional standalone feature panel while retaining the same backend API.

A trusted artifact registry resolves logical identity to certificate ARN, provider region and consumer bindings. The browser sends an approved operation, expected revision and idempotency key, never an arbitrary ARN/ACM request. An inspection adapter reads ACM descriptions and registered consumer state. The replacement adapter coordinates ACM issuance, validation, DNS and consumer association through the declared deployment mechanism; AppConfig does not change ACM certificates.

Separate certificate.inspect, certificate.replace and shared-identity certificate permissions. The worker gets scoped describe/tag/associate actions and narrowly justified request permissions where resource scoping is unavailable. DNS writes use a separate zone-bound capability; readers and application Lambdas receive no certificate-write credentials. Audit actor, target, public diff, job steps and errors without secrets.

## 5. Durable replacement and recovery

Acquire a per-certificate/consumer lease and compare registry revision plus observed fingerprints. Preserve unrelated names, tags and consumer settings. External changes cause a conflict/replan; a framework lease cannot lock an independent AWS operator.

Prerequisites include DNS authority, available quotas, correct region and an approved consumer/domain plan. Request and validate the replacement while retaining the functioning certificate. Poll issuance durably, with timeout and retry status distinct from failure. Retain ACM DNS validation CNAMEs while needed for renewal; shared validation records must not be deleted as cleanup for one replacement.

After issuance, associate the new certificate, wait for service deployment and verify HTTPS hostname/chain and consumer health. Record desired versus applied revisions and partial completion. Retain the previous valid association for a bounded recovery window. Rollback is a new checked association operation; an expired/deleted certificate cannot be restored by replaying its ARN.

Domain changes also require DNS, CORS, OAuth callbacks, bootstrap/client endpoints and passkey RP compatibility. Certificate issuance alone solves none of those migrations. Keep independent access available before modifying shared administrator ingress.

Pulumi owns current provisioning. Initially keep writes deployment-controlled. A future worker requires an explicit field ownership handoff and authoritative desired registry consumed by later deployments; avoid stale constants and blanket ignoreChanges. Never delete the old certificate before all associations and dependencies are reconciled.

## 6. Delivery and tests

Start with inventory/health and missing-binding diagnostics. Add same-name replacement only after durable jobs and deployment reconciliation exist; enable domain migrations last. Test wrong-region/hostname rejection, denied scopes, environment/shared isolation, retained validation records, conflicting writers, issuance timeout, partial association, retries, expired rollback targets and secret-free errors. Then use controlled HTTPS/read-back checks for each regional/edge consumer. No live issuance or migration is implemented here.

## 7. Provider references

- [ACM DNS validation and renewal records](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)
- [Managed renewal eligibility](https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html)
- [CloudFront certificate requirements](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html)
- [Regional certificate requirement](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-regional-api-custom-domain-create.html)
- [HTTP API regional custom domains](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-custom-domain-names.html)
