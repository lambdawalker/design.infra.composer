# Bedrock Mantle custom configuration panel

## 1. Status and source baseline

This proposes configuration contracts and a custom panel; it implements no inference changes. Follow the [configuration and administration policy](../configuration-and-administration.md). Application ownership suppresses the optional standalone panel.

Attestra accesses a managed model; it does not provision a dedicated model or inference endpoint. [Extractor at commit 4607807](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/awscapture/extractor.go) fixes `google.gemma-4-e2b`, uses AWS SigV4 with signing service `bedrock-mantle`, and derives `https://bedrock-mantle.{region}.api.aws/openai/v1/chat/completions` from transport configuration. There are no client-supplied endpoints or external API keys.

The request has a 55-second context budget, default HTTP timeout of 55 seconds, 4096 maximum completion tokens, high reasoning effort, nonstreaming response and `store: false`. It sends processed front/back images, constrains payload/response sizes and validates returned card JSON. The [capture worker IAM grant](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go) permits `bedrock-mantle:CreateInference` with Resource `*`, restricted by `bedrock-mantle:Model` equality. The worker timeout is 90 seconds; its lease is 120 seconds. These are not runtime properties.

## 2. Sections and useful controls

| Section/property | Proposed exposure | Independent risk |
|---|---|---|
| Application settings: capture requirement/enabled | Existing validated onboarding/capture policy | Consent and feature availability |
| Application settings: extraction purpose/disclosure | Declared policy consumers only | Sensitive-data processing and user understanding |
| Application settings: transcription/output acceptance | Versioned validated behavior, not free-form prompts | Incorrect or fabricated identity information |
| Artifact settings: model/access inventory | Initially read-only fixed-model view | Provider/account/region capability |
| Artifact settings: inference time/token budget | Later bounded adapter after consumer support | Truncation, timeout, cost and lease failures |
| Artifact settings: approved model selection | Future reviewed capability only | IAM, modality, quality and data-handling compatibility |
| Artifact settings: region/endpoint/auth | Deployment-controlled, read-only initially | Residency, service access and credential boundary |

Classification is semantic. Prompt/schema behavior is application configuration with high risk; its operating source, model access and execution budget are artifact configuration. Content editors receive no inference infrastructure rights.

Show account/region, environment/shared scope, worker role/function and deployed code revision, model ID, endpoint family/path, effective request limits, source binding, desired/applied revision and drift. Quotas can be shared across consumers.

## 3. Provider and safety boundaries

Current AWS documentation recommends `bedrock-runtime` for new Chat Completions applications and Mantle for required compatibility cases. Mantle route prefixes vary by model. Preserve the inspected source path as observed behavior, not a claim that it works for every model or region. Endpoint-family migration requires model-specific availability, authentication, API, quality and IAM verification; it is not a configuration-only substitution.

There is no generic regional fallback. Before approving any new model or deployment region, verify image support, exact model ID/route, account access, applicable quotas, legal/data-handling requirements and output contract. A failure must remain explicit rather than routing identity documents to another region/provider.

`store: false` is a request setting, not a comprehensive retention or consent guarantee. Preserve it initially and independently review provider terms, applicable account/project retention controls and organizational requirements. Keep image bytes, extracted identifiers, tokens and model responses out of diagnostics and configuration history. Existing untrusted-image prompt handling, strict JSON validation and user review remain mandatory; extraction does not prove identity.

## 4. Source and adapter design

First inventory compiled constants and deployed role policy without claiming a runtime reader exists. Future typed properties must declare supported consumer releases, bounds, unavailable-source behavior and rollout method. A managed registry can feed deployment or a newly implemented runtime reader; merely storing a different model ID cannot change compiled extractor code or IAM access.

An approved-model registry must bind model ID, endpoint family/path, allowed region, modality, tested output schema, request parameter support and exact IAM condition. Never expose arbitrary base URLs, arbitrary prompt text, role ARNs or access keys in the panel. Keep workload identity/SigV4; native service access is not an editable password field.

Separate application-policy editors, inference operators and IAM/deployment operators. The worker may inspect registered configuration; permission to change role policy is narrowly scoped to the declared role and approved statement. Preserve other statements and never drop the model condition because an update failed. Browser sessions receive no AWS credentials.

## 5. Jobs, authority and recovery

Changing compiled parameters initially means a deployment job. Future live configuration requires one desired registry consumed by Pulumi and the adapter. Preserve full environment maps and explicit version/alias targeting where a future binding uses them; do not imply immutable published versions update in place.

A durable job records expected revision, observed code/configuration/IAM fingerprints, affected releases, quality-evaluation reference and per-step results. Serialize related worker/policy changes and coordinate deployment ownership. Fingerprints detect drift but cannot provide atomic AWS cross-service writes.

Preview inference budget against the Lambda timeout, lease, SQS visibility and retry strategy. Insufficient token budgets can truncate output; larger outputs or longer inference can increase latency and duplicated charge exposure; do not add automatic inference retries without examining application/SQS retries. On partial IAM/consumer rollout, stop, record applied steps and recover only owned fields after re-reading. Restoring code/configuration cannot retract documents already submitted, reverse model charges or repair previously accepted extraction results automatically.

## 6. Delivery and verification

Begin with read-only inventory and missing-capability diagnostics. Implement bounded budgets only after a compatible reader/deployment contract exists. Add model selection last, using approved candidates and a privacy-safe evaluation corpus covering unreadable fields, prompt injection, accents, leading zeros, strict schema, truncation and timeouts.

Verify target isolation, fixed endpoint derivation, retained model condition, stale revisions, source failures, partial deployment and Pulumi reconciliation locally. Later controlled checks use synthetic documents and separately verify access, regional model availability and quality; HTTP success alone is insufficient. No production identity document is sent by saving settings.

## 7. Provider references

- [Chat Completions endpoint and route guidance](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-chat-completions.html)
- [Inference endpoint authentication and authorization](https://docs.aws.amazon.com/bedrock/latest/userguide/endpoints.html)
- [Mantle actions and model condition keys](https://docs.aws.amazon.com/service-authorization/latest/reference/list_bedrock-mantle.html)
- [Model availability discovery](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- [Bedrock data protection](https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html)
