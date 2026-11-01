# Configuration and administration

## 1. Status and revised direction

This document records the configuration rules agreed after the initial architecture discussion. It supersedes a blanket preference for environment variables and the earlier proposal that every feature UI must mount into a common JavaScript shell.

**Agreed:** features expose configurable properties; applications own their source bindings and configuration administration by default. A feature may provide a standalone panel, but that panel is not deployed when its application takes configuration ownership.

**Agreed priority:** most secure suitable approach, provider recommendation for the use case, then operating cost.

**Recommended:** the detailed schema fields, diagnostics, and adapter lifecycle below implement those requirements. Exact API names and some rollout policies remain open. All snippets are pseudocode. The Python local prototype does not yet implement these rules.

## 2. Property ownership and optional panels

| Mode | Configuration owner | Feature panel |
|---|---|---|
| Feature deployed standalone | Standalone composition/configuration manager | Optional; selected by standalone deployment |
| Feature included in application | Application, by default | Not deployed |
| Application explicitly delegates configuration | Selected feature/configuration manager | Deployed only when explicitly selected |

A property has one authoritative writer. Standalone and application modes use the same schema, validation, authorization, and change operations. A panel must not be the only implementation of the configuration API.

The application may build custom controls or generate forms from schemas. Configuration integration does not require mounting feature UIs, shared React/Vue/etc. dependencies, or a selected frontend framework. The earlier framework discussion was exploratory, not a requirement.

The app-owned panel and index retain their independently deployed/versioned lifecycle from the architecture. Configuration ownership does not require deploying the full feature again to change every setting; the selected update mechanism determines the operation.

### Dashboard sections — agreed

The admin dashboard has two clearly separated top-level sections:

| Section | Meaning | Examples |
|---|---|---|
| **Application settings** | What the application/feature does | Onboarding modes, permitted feature behavior, disclosure messages, approved business-service URL, application password rules |
| **Artifact settings** | How deployed resources execute, connect, and are operated | Lambda memory/timeout/concurrency, API Gateway throttles/CORS, database/storage settings, reader-source bindings, IAM and deployment controls |

Application settings are the ordinary feature-management area. Artifact settings are the infrastructure/operations area and must clearly identify low-level changes, affected resources and potential service disruption.

Classification is based on meaning, not storage. An application setting remains an application setting if delivered through an environment variable; choosing its reader source, execution identity or deployment mechanism is artifact configuration.

The value and mechanism may therefore have separate controls: the application section edits an approved logical property value; the artifact section manages how that property is delivered. Each shows a link to the other when useful without creating a second independent writer.

Use separate permissions and backend authorization, for example `application.settings.write` and `artifact.settings.write`, scoped by environment/resource and optionally property. An application editor does not automatically become an infrastructure operator. Hiding a tab is not authorization.

Both sections show the target application/environment or shared scope, current revision, change history and application status. Artifact edits additionally show the physical/logical resource, change scope, coupled operations and rollout/recovery impact.

Category and risk are independent metadata. Application settings can be security-sensitive: password rules, diagnostic response mode, proof lifetime, abuse controls and consent/retention need additional restrictions even though they affect application behavior. Conversely, artifact settings are not all equally dangerous. Validate permissions and review requirements for the specific change rather than assuming one section is inherently safe.

Properties should declare `category` (application/artifact), sensitivity, risk/impact, editable/read-only status and required permission. Default artifact controls are curated; do not expose arbitrary AWS fields or raw environment editing. The framework must reject unknown classifications where category is required and prevent callers from changing a property's category/permission to bypass authorization.

### Classification and coupled ownership — recommended procedure

1. Identify the logical value being edited. Feature/business policy is Application configuration; resource operation, source/reader/access or infrastructure binding is Artifact configuration.
2. Separate logical value from delivery/native mechanism where needed; link their controls without duplicating the authoritative field.
3. Evaluate sensitivity, change impact, scope and permission independently. A UI section is never a permission grant.
4. For coupled edits, produce one dependency-aware job requiring the union of the relevant capabilities, or explicitly approved service delegation. Preserve one owner for every field.

| Ambiguous case | Application value | Artifact mechanism / boundary |
|---|---|---|
| Service URL | Approved logical business endpoint | Env key, source binding, reader identity and rollout |
| Time limit | Business deadline/acceptance window | Lambda timeout and worker/queue timing |
| Parallel work | Business per-customer limit | Lambda reservation, mapping concurrency and provider capacity |
| Password rules | Product authentication policy | Native Cognito policy/client adapter and compatibility |
| Retention | Consent/purpose-driven retention policy | S3 lifecycle, DynamoDB TTL and cleanup execution |
| Diagnostic detail | Permitted application response content | Native log format/filtering and log retention |

An application policy may require native resource changes; category describes the property, not the API used to apply it. The feature contract proposes category and semantics; provider adapters declare operating constraints; application composition explicitly accepts a supported mapping. Conflicts fail validation rather than letting a request reclassify the field. Contract/policy owners resolve disagreements through a versioned change; dashboard users cannot override metadata to gain rights.

## 3. Separate declarations, consumers, and bindings

| Part | Declared by | Contains |
|---|---|---|
| Property contract | Feature | Logical name, type, constraints, sensitivity, required/default rules, freshness/rotation requirements |
| Artifact usage | Feature | Which artifact consumes which property and supported reader/application mechanisms |
| Application binding | Application | Source, location/key, initial value/reference, default policy, scope, access and update mechanism |
| Runtime reader | Framework/provider adapter | Source-specific retrieval, decoding, caching, validation and errors |
| Writer/change operation | Framework/provider adapter | Authorized updates, concurrency control, rollout, rotation and completion checks |

A logical property may have several artifact consumers. Bind sources per consumer when their constraints differ, or explicitly share a binding when appropriate. Validate the entire consumer set.

Example declarations:

```python
feature.configuration.url("validation_url", required=True)
feature.handler.uses_configuration("validation_url")
```

Example explicit binding:

```python
app.configure_feature(
    feature,
    properties={
        "validation_url": EnvironmentVariable(
            name="VALIDATION_URL",
            initial_value=email.validation_url,
            default=None,
        ),
    },
)
```

An initial value seeds the managed configuration. A read default is used when the selected source has no value under the declared policy. These are different concepts. A required property must not silently inherit a standalone default unless the application explicitly adopts it. An unavailable or unauthorized source is not automatically equivalent to a missing value.

Do not require literal secret defaults in manifests. Secret properties use protected references and explicit unavailable/missing-value behavior; never downgrade to an insecure fallback.

## 4. Stable artifact-facing interface

Artifact code reads logical names:

```python
url = configuration.get_url("validation_url")
api_key = configuration.get_secret("payment_api_key")
```

The application selects the implementation and supplies what it requires. A low-level binding might install an environment reader with its variable name and default, while the high-level application API accepts the feature's full binding set:

```python
app.set_feature_configuration_sources_and_default_values(
    feature,
    bindings=[...],
)
```

Both method names illustrate the requested model, not finalized API signatures.

An environment reader accesses local configuration. A remote/DB reader declares its provider client/extension, location, identity, access, timeout, caching and freshness policy. The feature should not hard-code source-specific SDK calls.

Treat sensitivity as independent of type: a URL can embed a token, username/password, or other confidential data. Classify by contents and purpose, not merely by a field being called a URL.

## 5. Source selection priority — agreed

Selection is per property, artifact, environment and relevant release scope:

1. Enforce functional and security constraints: sensitivity, access boundaries, encryption, rotation, freshness, artifact support, and read/write feasibility.
2. Among eligible approaches, prefer the strongest applicable security controls; do not trade unmet security requirements for price.
3. Prefer the provider-recommended method for that artifact and use case.
4. Optimize operating cost and latency among suitable choices, including caching and change frequency.

There is no universal security score that ranks every configuration service for every use case. Evaluate an actual storage/delivery/access/rotation arrangement.

The initial environment-variable cost preference is therefore conditional: use local reads for suitable nonsecret values, not for all properties. Never select a cheaper source by silently weakening requirements.

Allow explicit bindings as well as automatic selection. Explicit selection remains subject to mandatory validation. If no eligible source exists, fail before deployment; do not silently change classification, freshness, or source.

A proposed automatic binding:

```python
Property(
    name="payment_api_key",
    sensitive=True,
    required=True,
    max_staleness_seconds=60,
)

app.configure_feature(
    payments,
    properties={
        "payment_api_key": AutoSource(
            priorities=["security", "provider_guidance", "cost"],
        ),
    },
)
```

Cost estimates should state region, workload assumptions, storage/API charges, cache/concurrency behavior and rollout overhead. Unknown estimates must be reported as unknown, not presented as precise savings.

## 6. Distinguish storage, delivery, caching, and updates

A source binding is more than a storage name. Record:

- Authoritative storage and owning scope.
- Delivery/read adapter and any extension, client or local key.
- Reader identity and least-privilege permissions.
- Cache strategy, maximum acceptable staleness and refresh failure behavior.
- Writer identity, authorized changes and audit records.
- Change/rotation mechanism, propagation and completion semantics.
- Initial/default behavior and compatibility with affected releases.

An environment variable containing a secret's identifier is different from one containing the secret value. Copying a secret from Secrets Manager into Lambda configuration at deployment time does not preserve runtime secret retrieval/rotation semantics.

Sensitive data must remain protected through provisioning, state, execution, logs, previews, admin responses, and defaults. Pulumi secret marking remains necessary wherever a sensitive value enters Pulumi; encrypted local memory alone is insufficient.

Prefer provider-supported workload identities instead of static credentials when the target supports them. Keep secret material out of browser code and public discovery.

## 7. AWS Lambda baseline guidance

The table is the framework's proposed AWS policy informed by the linked provider guidance, not a claim that AWS recommends one service for every property.

| Property/use case | Preferred candidate |
|---|---|
| Database credential, API key, authorization token | Secrets Manager with an appropriate supported caching reader |
| Nonsecret URL/setting fixed for a deployment | Environment variable |
| Shared centrally managed key/value setting | Parameter Store with suitable retrieval/caching |
| Dynamic operational settings or feature flags | AppConfig with its Lambda extension |

AWS explicitly recommends Secrets Manager instead of environment variables for database credentials, API keys and authorization tokens. Parameter Store, AppConfig and Secrets Manager have different intended use cases; an encrypted Parameter Store value is not automatically a replacement for a secret lifecycle that requires rotation.

Secrets Manager integration can use the AWS Parameters and Secrets Lambda extension or a supported Powertools reader. Both can cache retrievals so the function need not call the remote service on every invocation. Configure refresh consistent with rotation and allowed staleness; caches are local to execution environments, not globally coherent.

AppConfig's Lambda extension is a different component: it retrieves application configuration, maintains a local cache, and checks for deployed updates. Propagation depends on the deployment strategy and polling. Neither secret caching nor AppConfig polling promises instantaneous fleet-wide updates.

Reader initialization must respect the selected SDK/extension lifecycle. Do not assume every Lambda extension endpoint is available during every initialization phase.

## 8. Configuration for applications versus AWS resource settings

AppConfig is a managed configuration store/delivery system with validation, controlled rollout and monitoring/rollback capabilities. Application code must consume its values. It is not a universal controller that directly changes all AWS resources.

| Example property | Application mechanism |
|---|---|
| Lambda business feature flag | AppConfig reader/cache |
| Database endpoint used by application code | Selected configuration reader |
| Database credential used by application code | Secret-aware reader |
| Lambda environment-backed setting | Function configuration rollout |
| Cognito password policy | Cognito management API or deployment adapter |
| RDS database instance size | RDS management API or deployment adapter |

Some changes must remain deployment-controlled even when displayed in an admin UI. Validate provider support, permissions, impact and completion instead of treating every edit as a database write.

AppConfig can source configuration from its hosted store and services including S3, Parameter Store and Secrets Manager. Custom AppConfig workflow extensions can import data from non-native sources such as RDS or DynamoDB. A database supplying configuration is different from AppConfig modifying that database's infrastructure settings. AppConfig workflow extensions are also distinct from Lambda reader extensions.

## 9. Lambda environment updates and retained releases

Published Lambda versions lock their environment variables. Changing an environment-backed property for published traffic is a configuration rollout:

1. Validate the request, target environment/release and affected consumers.
2. Read the authoritative current configuration and check the expected revision.
3. Preserve unrelated environment variables; AWS replaces the complete Variables map.
4. Update the unpublished function configuration using concurrency/revision protection.
5. Wait for the update to complete and check for failure.
6. Publish a new Lambda version with the intended code artifact and configuration.
7. Verify readiness and deliberately update the selected alias/routing.
8. Record desired/applied configuration revisions and the actual target version.

The code artifact may remain identical; code release, configuration revision, and AWS Lambda version are distinct identities. A configuration-only change does not by itself require a public API major bump.

Do not silently repoint exact release pins or imply an immutable version changed in place. The policy for targeting one selected release versus all compatible active releases is still open and must be explicit in a change plan.

One manager owns each function's full environment-variable map. Serialize coordinated updates and check revisions so two property edits cannot overwrite each other. Do not publish a configuration update from an unrelated code artifact that happens to be in the shared unpublished function slot.

A later Pulumi deployment must reconcile the declared configuration authority, not restore an obsolete bootstrap value. Changing ownership between deployment and runtime management requires an explicit handoff.

## 10. Authorization and administration

The application must have the components needed to read and change configured properties after deployment. Model roles/identities and permission plans, not necessarily long-lived IAM users.

- Artifact execution roles receive scoped read access.
- The configuration worker receives scoped write/rotation/deployment permissions.
- Human administrators authenticate to the application's configuration API with environment/property/action authorization.
- Browser code does not receive worker AWS credentials.
- Where a cloud API writes a whole resource rather than one property, the backend validates allowed keys and preserves unrelated values.
- Existing external credentials/access must be checked where feasible; provisioning a policy document alone does not prove effective access through every external control.

The [security and operational baseline](security-and-operations.md) specifies recommended secret custody/rotation, scope authorization, execution-time grant checks, panel/session defenses and independently protected audit evidence. IdP/vault backend choices remain open; existing artifact plans do not imply those framework services are implemented.

Standalone and application panels call the same validated backend operations. Record who requested a change, target scope, nonsecret diff/reference, expected/applied revision, status and error. Secret edits accept replacements without returning old secret values.

## 11. Deployment validation and clear diagnostics

Compare the feature's full property and consumer inventory against application bindings before cloud mutation.

Reject:

- Missing required mappings; unknown or duplicate properties.
- Unsupported sources/readers for an artifact.
- Invalid types, values, constraints or default policies.
- Unclassified sensitivity where the policy requires a classification.
- Missing source location/client/extension/identity requirements.
- Incompatible freshness, rotation or cache behavior.
- Environment-variable collisions and conflicting writers.
- Cross-environment/release bindings outside allowed scope.
- Missing required permission declarations or failed effective-access checks.
- Incompatible active-release schemas or unsupported update mechanisms.

Example proposed diagnostic:

```text
DEPLOYMENT BLOCKED [IC_CONFIGURATION_GAP]

Feature: Authentication
Artifact: Authentication.handler
Property: validation_url
Required type: URL
Declared at: authentication/configuration.py:18

No application source binding was supplied.
Bind the property or explicitly adopt an allowed standalone default.
No deployment was started.
```

Successful plans explain the selected source, policy version, reader/cache, writer/change method, permission scope, and why alternatives were rejected. Do not print secret values while explaining a decision.

## 12. Versioned policy and open choices

Provider adapters should contain documented recommendation policies with source links and review metadata. Record the policy version and resolved selection in deployment manifests. Review provider changes periodically during development; do not silently migrate live sources when framework policy changes.

Still open: final property/source schema and API names; precise scoring/comparison for eligible security arrangements; source-specific cache failure behavior; configuration rollout targeting across releases; adapter services and administrative UI implementation.

The local prototype remains unchanged by this documentation update. Future implementation must test source binding gaps, secret handling, provider selection, revision conflicts, cache freshness, permissions, panel suppression and retained-release behavior.

## 13. Provider references

- [Lambda environment variables and Secrets Manager recommendation](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [Secrets Manager retrieval/caching in Lambda](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html)
- [Parameter Store and configuration-service comparison](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [AppConfig overview](https://docs.aws.amazon.com/appconfig/latest/userguide/)
- [AppConfig Lambda integration](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions.html)
- [AppConfig extension cache and update behavior](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions-how-it-works.html)
- [AppConfig configuration sources](https://docs.aws.amazon.com/appconfig/2019-10-09/APIReference/API_CreateConfigurationProfile.html)
- [AppConfig non-native sources](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-configuration-profile-other-data-sources.html)
- [Cognito UpdateUserPool](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_UpdateUserPool.html)
- [RDS ModifyDBInstance](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_ModifyDBInstance.html)
