# Artifact configuration-panel catalog

## Scope and status

This catalog maps every artifact type identified in the [Attestra source inventory](attestra-configuration-plan.md) to a post-deployment configuration/custom-panel plan.

**Coverage: 16 artifact types. All entries are design plans, not implemented panels or deployed controls.** They apply the [shared configuration rules](../configuration-and-administration.md) to source snapshot `4607807ab0346f4a38532982889fe2e56954412e` of go.attestra.aws.auth, reviewed 2026-11-01. No live account inventory, infrastructure update, user operation or secret export was performed.

| Artifact type | Useful controls / plan focus | Detailed plan |
|---|---|---|
| Lambda | Memory/timeouts, concurrency, safe observability, supported application tuning and source bindings | [Lambda](lambda-configuration-panel.md) |
| API Gateway HTTP APIs | Stage/route throttles, approved browser origins, native update/ownership | [API Gateway](api-gateway-configuration-panel.md) |
| Cognito | App versus native identity policy, token/session settings, approved client changes, MFA/rotation compatibility | [Cognito](cognito-configuration-panel.md) |
| DynamoDB | Capacity/protection/backup/TTL controls, native table changes versus transactional configuration/business data | [DynamoDB](dynamodb-configuration-panel.md) |
| S3 | Evidence/state/association ownership, lifecycle/encryption/access, irreversible deletion boundaries | [S3](s3-configuration-panel.md) |
| SQS and event-source mapping | Visibility/redrive/retention, worker parallelism, pause/recovery and retry-layer coordination | [SQS](sqs-configuration-panel.md) |
| EventBridge scheduled rules | Schedule/enablement, fixed trusted targets, reset/dispatcher safety | [EventBridge](eventbridge-configuration-panel.md) |
| CloudWatch | Retention, alarm thresholds/destinations, telemetry/privacy controls and read-only diagnosis | [CloudWatch](cloudwatch-configuration-panel.md) |
| SES | Approved sender/delivery configuration, identity/DKIM dependencies, sandbox/readiness and controlled templates | [SES](ses-configuration-panel.md) |
| Bedrock inference dependency | Approved model/region/budgets, role access, quality/data handling and controlled inference changes | [Bedrock](bedrock-configuration-panel.md) |
| ACM certificates | Validation/renewal visibility and coordinated certificate replacement/association | [ACM](acm-configuration-panel.md) |
| DNS | Owned record edits, zone/provider binding, TTL/propagation and target coordination | [DNS](dns-configuration-panel.md) |
| CloudFront/OAC | Optional Android association hosting, cache/security/asset publication and safe propagation | [CloudFront](cloudfront-configuration-panel.md) |
| IAM/OIDC | Curated roles/trust, effective access, privilege-escalation prevention and independent recovery | [IAM/OIDC](iam-oidc-configuration-panel.md) |
| Admin/index web and discovery artifacts | Approved presentation/public projection, immutable builds, readiness-bound publication | [Admin/index](admin-index-configuration-panel.md) |
| Deployment tooling/state | Target/default memory, protected credential sources, operator jobs, state/vault migration and locks | [Deployment/state](deployment-state-configuration-panel.md) |

The inventory groups service bindings as artifacts even when the stack does not provision a new service instance (for example, Bedrock inference). Optional DNS/CloudFront paths remain optional; a plan does not imply an account has those resources.

## Shared dashboard contract

Two top-level sections:

- **Application settings:** feature behavior and logical values, including security-sensitive policies where explicitly supported.
- **Artifact settings:** resource execution, infrastructure, access, configuration-source bindings and operational controls.

Storage does not determine the section. An env-backed service URL can remain an application value; the source/key/reader binding is artifact configuration. Risk/sensitivity and required permission are independent of category. No application editor implicitly receives infrastructure or shared-control-plane rights.

Applications own integrated configuration by default. Feature standalone panels are optional and suppressed when the application takes ownership. All panels use the same backend property contract; hiding a tab or feature panel is not an authorization mechanism.

## Minimum contract for every panel

Each detailed plan must identify:

1. Source-derived current behavior and which proposed controls do not exist yet.
2. Typed editable properties, defaults/initialization, category, risk, scope and migration/read-only boundaries.
3. Reader or native service-management adapter, writer identity and permission plan.
4. Trusted artifact binding and complete property coverage before adoption/deployment.
5. Desired/applied/observed revisions, durable change jobs, read-back and relevant data-plane readiness.
6. Cross-artifact dependencies, partial failure, rollback limits and independent recovery.
7. One authority per field, with subsequent Pulumi/CLI/CI operations preserving adopted settings.
8. Security → applicable provider guidance → cost selection, with no insecure source fallback.
9. Local validation/tests and separately scoped future live checks; no secret values in documents/previews/logs.

## Cross-artifact changes

| Requested change | Coordinated contracts |
|---|---|
| Lambda worker timeout/parallelism | Lambda budget, SQS visibility/batch/redrive, account capacity, inference/downstream limits |
| Evidence retention | Consent/policy identity, stored record deadlines, cleanup schedules, S3 lifecycle/versions and data restoration limits |
| Identity origin/domain | DNS, ACM, API mapping/CORS, Cognito callbacks/RP, existing passkeys, public bootstrap and clients |
| SES sender | Identity/DKIM/DNS readiness, Lambda sender config, IAM FromAddress condition, Cognito delivery and templates |
| Inference model/region | Approved SDK endpoint/auth, IAM condition, client budget, output schema/quality, consent/data handling and regional availability |
| Runtime configuration publication | Environment grants, transactional history/consent checks, approved public projection, explicit freshness and any optional AppConfig activation |
| Application or control-plane release | Artifact hash/version, configuration revision, supported routes/discovery, client update policy and rollback dependencies |
| Operator credentials/state | Local vault versus hosted worker source, CI trust, backend owner/encryption/locks and recovery authorization |

A coordinated change is not a distributed transaction merely because it has one Save button. Plans show ordered operations and partial application. Some actions (deletion, credential changes, data expiry, external email) cannot be undone by restoring old configuration.

## Suggested implementation order

1. Build the common property/category/permission/ownership contract and read-only artifact inspection.
2. Add a small set of environment-scoped native controls, beginning with the existing Lambda/API Gateway plans.
3. Add sensitive lifecycle/data/identity workflows only with their compatibility and recovery tests.
4. Add shared-control-plane, IAM/DNS/state and migration workflows with separate operator authorization.
5. Add optional optimization/presentation controls once data-plane evidence, privacy and cost assumptions are available.

This order is a recommendation, not an authorization to implement or deploy the planned changes. It does not replace the broader [roadmap](../roadmap.md).
