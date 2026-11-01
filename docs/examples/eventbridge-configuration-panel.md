# EventBridge custom configuration panel

## 1. Status and source baseline

This is a proposed Attestra panel/adapter plan, not implemented functionality. Follow the [configuration and administration policy](../configuration-and-administration.md): the application owns configuration and its panel by default; an optional standalone feature panel is suppressed when the application takes ownership. Both use the same backend contracts.

At [commit 4607807, capture infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go), `capture-sweep` invokes the capture dispatcher with `rate(1 minute)`. [Reset infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/reset.go) declares another one-minute rule targeting the reset Lambda with fixed input `{"action":"work"}`. Both grant `events.amazonaws.com` Lambda invocation restricted by rule ARN. Target retry policies and EventBridge delivery DLQs are not explicitly configured.

These are scheduled **rules**, despite Pulumi's `cloudwatch` package name. They are not EventBridge Scheduler resources. AWS recommends Scheduler for new scheduling use cases, but migration requires an explicit design; this panel must not promise Scheduler timezone, flexible-window or one-time scheduling features on these rules.

## 2. Sections and useful controls

| Section/property | Proposed treatment | Independent risk |
|---|---|---|
| Application settings: capture enabled, onboarding requirement | Existing runtime policy; link to capture panel | Security/consent impact even though application behavior |
| Application settings: reset eligibility | Existing deployment policy; separate reviewed capability | Destructive behavior; never implied by schedule enablement |
| Artifact settings: capture cadence | Bounded rate/approved UTC cron after backlog and cleanup analysis | Delayed dispatch/cleanup or increased invocation load |
| Artifact settings: enabled state | Explicit pause/resume with backlog impact | Availability; pausing does not cancel already delivered work |
| Artifact settings: delivery retry age/attempts | Advanced bounded target controls | Duplicate/stale delivery and recovery tradeoff |
| Artifact settings: delivery DLQ | Later approved queue binding with resource-policy validation | Sensitive payload retention/access |
| Artifact settings: reset rule | Read-only initially; separately privileged operational plan | May resume pending destructive work |

Show account, region, environment, rule ARN/name, target ID/ARN, declared expression, effective state, desired/applied revision, writer and drift. Shared resources require a distinct scope and permission; the environment picker cannot retarget them silently. Validate cleanup deadlines and capture leases before permitting slower cadence. Scheduled rules have minute precision and UTC cron semantics, not an exact execution-time guarantee.

## 3. Binding and adapter

Declare typed logical properties such as `capture.sweep_interval` with category `artifact`, impact, bounds, consumer inventory and permission `events.rule.configure`. Resolve rule and target identities from trusted deployment outputs. The browser sends logical changes and expected revision, never arbitrary ARNs or AWS request bodies.

The managed desired record is the future authoritative source. A native reader uses DescribeRule and ListTargetsByRule; the writer uses approved EnableRule/DisableRule, PutRule and PutTargets operations. AppConfig or a runtime database alone cannot reconfigure a rule. Source bindings, worker identity and operating mechanism belong in Artifact settings even when the schedule implements application behavior.

PutRule can clear omitted properties. Construct a supported complete request from observed settings, preserving unrelated event pattern, description and state. PutTargets requires preserving the exact registered target configuration, including fixed reset input; reject unknown security-critical fields. Do not expose target replacement, arbitrary input transformers, cross-account buses or role selection through a generic form.

## 4. Permission and change lifecycle

The browser calls an authenticated configuration API. Application editors do not inherit EventBridge rights. Grant the worker describe/list and narrowly selected mutations on registered rule resources; enforce target/property allowlists in the backend where IAM is broader. Initial capabilities need no rule deletion, arbitrary Lambda invoke, IAM PassRole or reset-data permissions. A delivery DLQ addition is a coordinated queue-policy/deployment capability.

A durable job authorizes environment/resource/property, takes a per-rule lease, compares registry revision and observed fingerprint, records the nonsecret diff, applies approved operations and reads back rule and targets. Fingerprints are conflict detection, not native AWS compare-and-swap. Serialize deployments through the same coordinator; external writers can still race.

Pulumi currently owns these declarations. Before live editing, either route changes through a deployment job or hand the selected fields to a registry consumed by both deployment and worker. Never let the next deployment restore hard-coded one-minute settings unexpectedly.

## 5. Failure, retries and recovery

EventBridge delivery retries cover failure to deliver to Lambda. Lambda asynchronous execution retries, capture application retry/lease logic and SQS visibility/redrive are separate layers; one successful delivery does not prove successful processing. The existing capture SQS DLQ is not an EventBridge target-delivery DLQ. Display each layer separately and avoid multiplying retries without assessing duplicate processing.

Inspect PutTargets `FailedEntryCount` and per-entry errors even on a successful HTTP response. Persist partial completion if a rule update succeeds but target update fails. Re-read and restore only owned fields after conflict checking; allow propagation time. Restoring cadence/state cannot retract invocations, undo processed captures or restore reset-deleted data. “Run now,” reset triggering and DLQ replay are separate operations, excluded from settings saves.

## 6. Delivery and verification

Begin with inventory, scope and drift inspection. Then enable bounded capture pause/cadence changes with durable jobs and deployment reconciliation. Add delivery retries/DLQ only after queue-policy and failure tests. Keep reset writes behind an independent destructive-operation capability.

Verify source bindings, permission isolation, preserved target input, stale revisions, external drift, partial target failure, delayed propagation, paused backlog and duplicate delivery in local/mock tests. Later controlled environment checks must separately confirm native read-back and dispatcher processing; never trigger an environment reset as a smoke test.

## 7. Provider references

- [Scheduled rules, precision and Scheduler recommendation](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)
- [PutRule replacement semantics](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutRule.html)
- [PutTargets partial failures and target policies](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutTargets.html)
- [Target delivery retries](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html)
- [Lambda asynchronous errors](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html)
