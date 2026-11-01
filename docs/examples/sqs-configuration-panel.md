# Attestra SQS configuration panel plan

## 1. Status and current source configuration

Proposed adapter and custom-panel capability only; no queue, message or cloud deployment is changed. Source reviewed at [Attestra commit 4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e), with AWS guidance checked on 2026-11-01. Follow [configuration policy](../configuration-and-administration.md) and [artifact inventory](attestra-configuration-plan.md).

| Artifact | Current declaration |
|---|---|
| Environment capture-validation queue | Standard queue; visibility 720 seconds; SQS-managed encryption; redrive to capture DLQ after maxReceiveCount 5 |
| Capture-validation DLQ | SQS-managed encryption; retention 1,209,600 seconds (14 days) |
| Lambda mapping | Batch size 1; ReportBatchItemFailures; maximum concurrency defaults to 2 |
| Worker | 90-second timeout, 1024 MB; function reservation configurable independently |
| DLQ alarm | Maximum visible messages greater than zero over one 60-second evaluation; missing data not breaching |

Evidence: [queue/worker resources](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), [concurrency parsing](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture_concurrency.go), [partial-batch handler](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/cmd/capture-worker/main.go). Source queue retention is omitted: inspect the effective value rather than presenting AWS's four-day default as an explicit declaration. Production concurrency settings require explicit positive reservation and worker maximum; show resolved values, not only defaults.

## 2. Application settings versus Artifact settings

**Application settings** control capture admission, consent and supported retry behavior. A per-capture retry is a data operation with ownership/state checks, not a global settings edit. Existing [application Retry](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/capture/service.go) changes durable work, generation/revision and attempts under application conditions.

**Artifact settings** control queue visibility/retention, redrive policy, encryption, polling, mapping batch/concurrency and runtime IAM bindings. Category follows meaning, not where values are stored; application editors do not inherit queue-management permission. Retention reductions are artifact configuration with destructive potential.

SQS-triggered Lambda uses synchronous polling invocations. Generic Lambda asynchronous maximum-event-age/retry settings are not the retry controller for this queue. Queue redelivery, DLQ transfer, dispatcher rescheduling and the application's own bounded attempts are different mechanisms.

## 3. Useful typed properties and limits

| Property | Proposed exposure and purpose |
|---|---|
| `visibility_seconds: integer` | Bounded advanced edit; balance processing headroom against delayed retry |
| `retention_seconds: integer[60,1209600]` | Independent source/DLQ values; preview backlog at risk before shortening |
| `max_receive_count: positive integer` | Bounded policy control; initially preserve baseline 5 and prevent arbitrary DLQ reassignment |
| `mapping.maximum_concurrency: integer` | Coordinated Lambda mapping property; bound to effective worker/account capacity |
| `mapping.batch_size: integer` | Later tested capability; preserve partial-failure semantics and workload envelope |
| Encryption, queue type/identity, redrive destination/policy | Inspect initially; explicit access/migration operation for changes |

Proposed `ManagedResourceProperty(adapter="aws.sqs.queue", property="visibility_seconds", units="seconds")` declares category, permission and risk. The adapter uses approved `GetQueueAttributes`/`SetQueueAttributes`; mapping changes use the Lambda adapter. No arbitrary JSON policies, queue URLs or AppConfig writes stand in for native management.

## 4. Coupled timing and delivery semantics

[AWS recommends visibility at least six times the Lambda timeout](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html), plus any batching window. Current 720 seconds exceeds six times 90 seconds. Validate this envelope and the native timeout constraint whenever either resource changes. Mapping concurrency must fit reservations and downstream capacity; batch size changes affect memory, duration and partial-failure handling.

[Worker state](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/capture/worker.go) uses a 120-second lease with revision/generation fences and durable due work. Do not tune Lambda runtime beyond lease assumptions without changing/testing worker logic. Standard delivery remains at least once; duplicate/stale jobs must remain harmless. Queue retries cannot recreate expired/deleted evidence or bypass capture-state validation.

[Standard DLQ retention](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) runs from original enqueue time; transfer does not grant a fresh full 14 days. Keep DLQ retention longer than source retention. Approximate DLQ age is not the original enqueue age.

## 5. Custom-panel and durable native workflow

1. Inspect account/region, environment, logical source/DLQ pair, mapping/worker, effective attributes, backlog/age, revisions and drift.
2. Choose typed settings and preview coupled timeout/concurrency changes, backlog loss, producer/consumer effects and rollout sequence.
3. Backend authorizes target/property/action and expected revision; resolves registered resources and persists an idempotent job.
4. Acquire queue/mapping coordination leases; read attributes and normalized fingerprints, rejecting preview drift.
5. Apply dependency-aware steps: expand visibility before increasing timeout; decrease timeout before reducing visibility; coordinate mapping limits with function capacity.
6. Poll/read back effective attributes/mapping, then record applied revision, observed results and remaining partial failures.

[SetQueueAttributes](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html) changes can propagate asynchronously; retention changes can take up to 15 minutes and expire older messages. Persist step state so worker restart resumes inspection rather than assuming atomicity. There is no native resource-wide revision lock; internal fingerprints cannot eliminate races with external writers.

## 6. Redrive, purge and retry are separate actions

**DLQ redrive** uses a separately authorized [message-move task](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue-redrive.html), approved same-environment destination and bounded rate. Confirm the underlying failure is repaired; show task progress/cancellation. AWS redrive resets message IDs/enqueue times, cannot filter/modify messages during the task, and cancellation leaves already moved messages in the destination.

**Purge** destroys messages, including in-flight messages, and can affect new messages during its deletion window. [PurgeQueue](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_PurgeQueue.html) can take 60 seconds and rejects another purge within that interval. It is a destructive incident/reset capability, never a retry button or settings-save side effect. It has no message-level rollback.

**Application retry** operates on one permitted capture and its current generation. Bulk redrive is not equivalent; stale jobs may correctly no-op. Do not receive messages merely to show a diagnostic preview: receiving changes visibility and receive counts. Keep sensitive message bodies outside ordinary settings views.

## 7. Ownership, permissions and delivery

Pulumi currently owns queues, mapping and policies. Establish field-specific authority and deployment reconciliation before writes; preserve accepted values on redeploy without blanket resource ignores. Keep queue URL/ARN, FIFO conversion, deletion/replacement, cross-environment reassignment and arbitrary policy changes migration-controlled.

Separate application editor, queue configurator, mapping operator, redrive and purge capabilities. Worker IAM grants only required attribute operations on registered queues; redrive needs move-task plus source receive/delete/attribute and destination send permissions, with KMS permissions if applicable. Browser credentials remain application-scoped. Runtime send/receive permissions remain distinct.

Phase one provides inspection; phase two bounded timing/retention controls; phase three coordinated mapping and incident workflows. Tests cover shared/environment isolation, permissions, stale revisions, external drift, timing/lease constraints, partial update recovery, retention loss preview, duplicate jobs, partial-batch failures, redrive cancellation, purge boundaries and Pulumi preservation. Live purge/redrive is not part of documentation validation.
