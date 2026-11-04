# Artifact report protocol, version 1

The same safe report model drives three outputs: JSON for machines, Markdown for deployment documentation, and one self-contained HTML page for inspection. A feature preview describes what it would deploy. A deployment report records what the host tried, when it ran, the planned changes and the evidence it could collect. All three formats must describe the same snapshot.

## Interchange

The [JSON Schema](../conformance/report-v1.schema.json) describes the reference writer's shape. Use UTF-8 JSON, case-sensitive field names and timestamps with offsets (RFC 3339). Zero time in the reference is `0001-01-01T00:00:00Z` and means unavailable. The reader should accept older v1 reports without configuration. Readers must check schemaVersion before normalization. A schema-valid report still requires the evidence, scope and configuration checks below.

| Record | Fields and meaning |
|---|---|
| Report | schemaVersion = 1, scope, metadata, cacheLoaded, optional warnings (stable safe codes), artifacts |
| Scope | application, repository, environment, account, region, project, backend, stack. Compare all eight strings including missing/empty values. |
| Metadata | revision, dirty, operation, outcome, startedAt, finishedAt. Preserve actual outcomes including failed attempts. |
| Artifact | key (logical identity, usually a URN), name, type, provider, providerId (physical identity), owner (creating repository), feature (canonical feature ID), parent (logical key), priority (ascending integer), plannedAction, observation, optional configuration |
| Observation | status, source, observedAt, reason. The timestamp belongs to that observation. A replacement can be planned while the old physical resource is present. |
| Configuration | source = pulumi-state, observedAt = state read time, values = map of field to canonical text. Presence and configuration have independent timestamps. |

Hosts may add explicit GitHub environment and DNS record entries. Inventory the S3 bucket as a main artifact and its files as children. A child's evidence belongs to that child. Authorize access to reports containing environment-specific identifiers.

## Evidence collection

| Source | Operation | Evidence it can establish |
|---|---|---|
| Offline catalog | Run constructors with isolated mock outputs or declare a static catalog | Desired identities, unknown presence, empty provider IDs |
| State export | Read managed records in deployment.resources | Recorded with original ID and read time. A state record alone cannot establish live presence. |
| Preview | Read resourcePreEvent metadata, including intended action | Preserve existing IDs, add planned resources with empty IDs, resolve parents after consuming the stream. Desired outputs cannot establish recorded settings. |
| Read-only refresh | Consume completed resourceOutputsEvent from refresh in preview-only mode | same/update with exact new.id proves present. delete with exact old.id and no new state proves absent. |
| External probe | Read the exact scoped GitHub, DNS or other provider identity | Verified presence or authoritative absence. Missing permission, unsupported types and incomplete responses yield unknown. |

Use the marked read-only refresh stream exclusively for refresh evidence. Ordinary deployment events can use the same operation names. Ignore pre-events, summaries, diagnostics and parent completions as proof of presence. Preserve verified completions on partial failure and mark unchecked items unknown. Execute the CLI through an injected runner, use a private temporary event log and remove it afterward. The host supplies authentication. Keep provider errors out of public output.

Omit stack, provider and component records. Prefer an explicit managed parent. Otherwise resolve known relationships (bucket, API, role, function, user pool, rule, secret, domain) against unique IDs or plain ARN outputs of the expected parent type. An ambiguous match leaves the relationship unresolved. The ARN lookup index is private to the adapter. S3 objects may use their key as display name. For standalone catalog reconciliation require a selected source scope and a unique feature/type/logical-name match on each side. Use the URN suffix for the logical name even when the display name is a file path.

## Safe recorded settings

Copy only the following fields from **outputs**. Use exact type identifiers. Omit wrapped secrets, nulls, objects, arrays and unsupported fields. Numeric settings require finite, exactly integral JSON numbers and are rendered as decimal integer strings. Boolean settings require JSON booleans and use lowercase text. Drop invalid entries individually and omit an empty configuration. Normalize user-supplied configuration through this same allowlist. Do not infer defaults or units.

| Resource type | Accepted output fields |
|---|---|
| aws:lambda/function:Function | memorySize, timeout, reservedConcurrentExecutions |
| aws:sqs/queue:Queue | visibilityTimeoutSeconds, messageRetentionSeconds, delaySeconds, receiveWaitTimeSeconds, maxMessageSize |
| aws:cloudwatch/logGroup:LogGroup | retentionInDays |
| aws:dynamodb/table:Table | readCapacity, writeCapacity (integers), deletionProtectionEnabled (boolean), billingMode (PROVISIONED or PAY_PER_REQUEST) |

Expose only safe identifiers and these settings. Never serialize raw state, provider diagnostics, policies, environment maps, secrets or S3 file contents. HTML and Markdown must escape values for their rendering context.

## Normalization, cache and hierarchy

1. Copy inputs. Drop empty keys and keep the first duplicate logical key. Sort by priority then key and sort warnings. Normalize unknown statuses to unknown. A timestamp is required for present, absent or recorded. Invalid evidence yields unknown/invalid_evidence. Unknown without a reason gets unchecked. Other supported reason codes are check_failed, not_found and identity_changed.
2. During merge, a scope mismatch returns the current inventory alone. For matching scopes, set cacheLoaded. Reuse an old observation only for the same logical key, provider and **nonempty identical physical ID** when the current observation is unchecked and undated. A dated failed check supersedes cached success. Retain cache-only artifacts, clear their old planned actions, then normalize again. Hosts with a complete authoritative inventory can exclude obsolete cache-only entries. Do not advance an observation's timestamp on load.
3. Store snapshots privately using atomic replacement in a scope-specific location. For shared Go cache directories the filename is the lowercase SHA-256 of the compact JSON Scope encoding plus .json. Use the Scope field order above, omit empty strings, and match the reference JSON string escaping. Verify the decoded scope and version on read regardless of filename. Offline reports may read a selected cache without writing mock evidence into it.
4. Preserve orphans as roots and break parent cycles deterministically. In sorted artifact order follow parent links, sever the first back edge in each walk, then attach siblings in sorted order. Exact feature selection includes the selected artifacts' ancestor closure and preserves ownership.

## Human interfaces

Show deployment scope, outcome, revision, timing, counts and evidence age before details. Place application and feature repositories in the overview. Initially collapse cards and show artifact name, type glyph, status text/color and short owner. Expanded cards show the qualified owner, physical/logical identity, planned action, evidence and recorded settings with their separate timestamps. Keep S3 objects and similar children under their parent.

The Pulumi priority profile tests lowercased type substrings in this order: domain/endpoint/distribution = 10, bucketobject/policyattachment/permission/route/integration = 60, bucket/table/secret/role/policy/userpool = 20, function/api/queue/rule/schedule = 30, other = 40. Adapters may provide an explicit priority. Sort within siblings by importance, owner, type, name, status or feature and allow reversing direction.

Search uses a case-insensitive substring of a card's own name, key, qualified owner, type, status or feature. Combine search and exact status/owner/type/feature filters with AND. A matching child retains ancestor context. A directly matching parent includes its descendants. Context alone never reveals unrelated siblings. Distinguish direct-match count, visible count, empty inventory and no matches. Reset filters independently of sort/disclosure. Provide accessible status text and usable native disclosure without scripts.

An authenticated host can expose a per-environment read-only explorer over a published snapshot. Check the environment grant before the read. Reload displays the latest saved snapshot and its original timestamps. The whole-snapshot download is independent of display filters. Snapshot publication, size limits, iframe policy and dashboard routes belong to the host. For a concrete integration see [Attestra's explorer](https://github.com/lambdawalker/go.attestra.aws/blob/main/docs/artifact-explorer.md).
