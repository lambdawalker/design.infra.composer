# Resource ownership, tags and visible labels

Every deployment supplies nonsecret application, environment, domain and deployment identifiers. Features supply a stable feature identifier and each resource's logical component name. Environment-scoped resources use their selected environment; shared admin/index and state resources use `shared`, never an arbitrary environment that happens to deploy them first.

## Canonical tags

| Key | Example | Owner |
|---|---|---|
| ic:application | attestra | Application |
| ic:environment | dev or shared | Application |
| ic:domain | attestrabond.com | Application |
| ic:feature | authentication or email-verification | Feature scope |
| ic:component | email-signup | Resource declaration |
| ic:deployment | attestra-dev | Deployment |
| ic:managed-by | infra-composer | Framework |

The application chooses an explicit hostname for domain; do not infer a registrable root domain by removing labels. It may use a common base domain or the deployed hostname. The identifier is not a URL and contains no credentials, paths or query parameters. Deployment identifiers remain stable across code releases; versions and revisions belong in deployment records. Tag values must contain no credentials or personal data.

Canonical keys cannot be overridden by a feature or by unrelated provider defaults. Preserve unrelated tags supplied by the resource declaration. Before applying labels to existing IaC resources, reconcile out-of-band operator tags into the desired configuration or configure AWS provider ignoreTags for agreed operator-owned keys/prefixes; the generic native transformation does not fetch them from AWS. CLI bootstrap labeling reads and merges actual existing tags. Conflicting ownership requires an explicit adoption/migration, not silent reassignment. Tags identify ownership but do not themselves grant permissions or authorize destruction.

## Descriptions and physical names

When the service and provider support a mutable description/comment, use exactly:

```text
index.attestrabond.com SHARED | go.attestra.aws
dev.attestrabond.com DEV | go.apexfission.aws.auth
```

The fields are the configured ownership domain, uppercase environment, and the repository of the feature/application that required the resource. The owner is independent of the existing canonical feature tag. Omit the resource name and purpose. Replace previous generated descriptions rather than appending them. Use ASCII separators for IAM compatibility. Validate service length limits and fail rather than silently truncate. Do not modify immutable descriptions, notably IAM managed-policy descriptions, merely to label a resource.

Existing physical names, ARNs, Pulumi names/parents and dependencies must remain unchanged. A separate migration is required before changing identifiers that might replace resources.

## Capability and inventory rules

Tag support must be established for the specific AWS resource/provider schema, not assumed from its service or parent. Apply tags directly to supported resources; do not rely on universal inheritance. Examples include Lambda functions, HTTP APIs/stages, DynamoDB tables, S3 buckets, SQS queues, Cognito pools, IAM roles/policies, secrets, EventBridge rules, ACM certificates and CloudFront distributions.

HTTP API routes/integrations, Cognito clients, inline IAM policies, secret versions and individual Route 53 records need their own inventory rows and parent references. AWS supports SES identity tags via SESv2, but the current legacy Pulumi SES domain-identity/DKIM adapter does not expose tags. Record that provider limitation as inventory-only; do not replace a live identity merely to change adapters. IAM attachments, certificate-validation helpers and S3 bucket configuration resources also remain visible in inventory even if they cannot be tagged directly.

Export `resourceInventory` for every owned native resource with type, logical name, Pulumi URN, provider ID, ownership labels, tagging coverage, description field and parent identifier/URN where applicable. Keep identifier outputs deferred during preview. Never serialize constructor arguments, environment variables, secret values, policies or document contents into this inventory. Explicit external references, such as a reused account-wide GitHub OIDC provider or operator-selected KMS key, are not implicitly application-owned and must not be relabeled.

Adapters must have mock coverage proving every registered native resource appears in inventory, supported resources receive canonical tags, and child resources retain parent references. Tagging exceptions must be reported rather than presented as successful AWS tags. Inventory helps discovery and maintenance; it is not permission to delete resources.

## Implementation and rollout

The Go core implements `ownership.Metadata`. The optional Pulumi adapter implements `awslabels.Install`, `ForFeature`, `Ensure`, `Option` and inventory export. Resource-specific options apply the labels to every configured AWS provider, including cross-region providers. SDK argument schemas determine available tag inputs; an explicit allowlist determines mutable descriptions. Generic core/runtime code imports no Pulumi or AWS SDK.

The application installs a scope and selects feature ownership at composition boundaries. Native standalone entry points use validated project/environment/origin defaults when no scope was installed. Existing embedding callers can install an explicit scope. Every native AWS constructor must forward the ownership option; mock coverage guards against omissions. No ambient global feature selector is permitted.

The Attestra bootstrap also tags its two state buckets as shared and tags its setup-owned deployment IAM role. Preserve other tags, reject foreign ownership, use JSON to encode arbitrary operator tag values and verify IAM read-back. State buckets use the stable shared index/ownership domain across environments. Existing external KMS keys and reused global OIDC providers are not claimed. The native inventory covers Pulumi-managed resources; bootstrap resources additionally remain recorded in existing wizard state/checkpoints and discoverable by tags.

Deployment IAM must include the service-specific tagging operations and any mutable description update operation. Keep resource scopes bounded. Apply metadata changes through reviewed previews; this standard does not execute a live deployment, rename resources, migrate state or rotate secrets.

## Provider references

- [AWS tagging practices](https://docs.aws.amazon.com/tag-editor/latest/userguide/best-practices-and-strats.html)
- [API Gateway taggable resources](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-tagging-supported-resources.html)
- [Cognito tagging](https://docs.aws.amazon.com/cognito/latest/developerguide/tagging.html)
- [IAM role description constraints](https://docs.aws.amazon.com/IAM/latest/APIReference/API_UpdateRoleDescription.html)
- [Route 53 tagging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/tagging-resources.html)
- [SESv2 identities](https://docs.aws.amazon.com/ses/latest/APIReference-V2/API_CreateEmailIdentity.html)
