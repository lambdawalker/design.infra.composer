# Admin/index web artifacts: configuration and custom-panel plan

## 1. Scope and current source

Applies the [configuration rules](../configuration-and-administration.md) to Attestra's web assets, public bootstrap/configuration and environment discovery. Source: [4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e), reviewed 2026-11-01. Proposal only; no UI, credentials or live endpoints changed.

The shared admin is HTML/JS/CSS embedded in a Lambda and served through its HTTP API, not the optional CloudFront association distribution. [Assets](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/adminapi/assets.go) and [handler](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/adminapi/handler.go) define this boundary. Public `/settings` returns issuer, clientId, origin and loginDomain; these are public identifiers, not an AWS credential channel.

The [index](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/registry/registry.go) publishes a narrow environment configuration: API URL, region, public Cognito pool/client identifiers and capture availability, with configuration hash/revision. Deployment writes use a signed IAM-protected change/lease protocol. [Runtime configuration](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/api.go) is a separate public no-store document backed by DynamoDB, not AWS AppConfig.

## 2. Worth opening after deployment

| Section | Property | Proposed treatment |
|---|---|---|
| Application settings | Existing onboarding/disclosure behavior | Keep existing schema, authorization, transactions and policy identity |
| Application settings | Display labels, helpful descriptions, ordering of environments in the human directory | Future presentation-only schema; do not confuse a label/order change with routing or authorization |
| Application settings | Approved links/help text/localization | Optional constrained schema with escaping and approved destinations; no executable HTML/JS or arbitrary external scripts |
| Artifact settings | Public discovery endpoint binding per environment | Deployment-controlled publication after target readiness and identity checks |
| Artifact settings | Admin issuer/client/login/origin bindings | Coordinated Cognito, gateway, DNS/CSP/callback change, not a free-form runtime textbox |
| Artifact settings | Cache/update policy and supported document schema | Explicit compatibility/rollout change; retain no-store protections for sensitive control-plane behavior |
| Artifact settings | Web build/release selection | Immutable build/hash and controlled deployment/rollback; current assets require a Lambda code update |
| Artifact settings | Enabled administration capabilities | Registered backend permissions/capabilities, not a browser-only navigation toggle |

Labels/branding are candidates, not fields the source already implements. Environment visibility has two meanings: cosmetic directory listing versus security authorization. Hiding an entry does not revoke API access; the panel must not imply otherwise.

## 3. Panel and module ownership

Keep the two top-level sections **Application settings** and **Artifact settings**. The application owns configuration UI by default; suppress a feature's standalone panel when integrated, preserving needed backend/history/identity services. No common React/Vue module runtime is required.

A custom panel selects application and environment or explicitly shared scope; it shows document schema, managed/applied/observed revisions, public projection and pending jobs. Presentation edits preview the sanitized result. Deployment-facing edits show target readiness and client compatibility; shared-admin changes require separate rights.

Prefer an explicit property inventory rather than exposing all configuration under one public endpoint. Public bootstrap/discovery has an allowlist. Internal resource inventory, roles, evidence locations, credentials, proof material and secret references remain private unless a separate intentional public contract requires a field.

## 4. Write/read paths

Presentation/runtime changes: authenticated panel → existing or new typed configuration API → environment/property authorization → conditional transaction/history → approved public projection. Preserve current consent snapshots and grant checks.

Discovery changes: panel submits a deployment/publication job → trusted worker validates deployed endpoint/region/pool/client associations and artifact readiness → existing lease/revision protocol → atomic authoritative index entry publication/read-back. A verified URL format alone does not prove it is the intended live backend.

Control-plane build or bootstrap changes use the deployment adapter. Do not promise instant runtime editing of embedded JS/CSS, or load arbitrary script URLs supplied as configuration. A UI change must retain compatible discovery/configuration contracts for supported clients.

Readers use HTTPS, expected schema and environment binding. The current admin APIs/assets use no-store and restrictive security headers; retain them until an explicit compatible cache plan exists. An old public document may survive in a client's cache; define supported refresh/staleness and update handling rather than claiming immediate fleet-wide switch.

## 5. Permissions, safety and recovery

Separate presentation/application editors, environment publication operators, shared-control-plane operators and deployment workers. Existing runtime grant management does not authorize endpoint substitution or issuer changes. Browser code receives no AWS/deployment credentials.

Preserve same-origin write checks, dedicated admin access-token issuer/client checks, PKCE flow and token-storage protections. UI risk is independent of section: a malicious help link or issuer substitution is dangerous even without an infrastructure API call.

Serialize public routing/publication with deployment and reset workflows. Use expected revisions, trusted resource bindings and immutable job/build identifiers. Keep desired/applied/observed states distinct when asset deployment and discovery publication fail separately. Do not overwrite a newer publication during rollback.

Index or UI rollback does not recreate removed backend releases, revoke issued tokens or reverse user actions. Keep independent operator recovery outside the possibly broken admin UI.

## 6. Delivery and verification

1. Register existing public/private schemas and ownership; display read-only effective context.
2. Add constrained presentation metadata only where useful; validate escaping, destination allowlists and unknown fields.
3. Add custom-panel publication jobs reusing the existing signed lease/revision protocol and readiness checks.
4. Add immutable control-plane build rollout and compatibility monitoring before changing cache/update behavior.

Test environment confusion, unauthorized shared edits, malicious URLs/HTML, unknown-schema rejection, secret exclusion, stale leases/revisions, partial build/publication failure, backend mismatch, old clients and independent recovery. Verify existing runtime/grant/consent semantics rather than replacing them with an eventually consistent generic editor.

No deployed UI or protocol change is implemented here.

## References

- [Source admin security/public contract](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/docs/admin-runtime-config.md)
- [Source index protocol](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/docs/environment-index.md)
- [Cognito plan](cognito-configuration-panel.md)
- [API Gateway plan](api-gateway-configuration-panel.md)
