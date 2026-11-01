# CloudWatch custom configuration panel

## 1. Status and observed baseline

This proposed documentation adds no monitoring resources or workers. Apply the [configuration and administration policy](../configuration-and-administration.md): the application owns its panel; standalone feature panels remain optional and are suppressed under application ownership. Backend APIs remain reusable independently of the UI.

Attestra attaches AWSLambdaBasicExecutionRole to Lambda roles in [application infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [capture infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/capture.go) and [reset infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/reset.go). These use Go custom runtime `provided.al2023`. The examined declarations do not manage log-group retention or alarm notification actions; inspect actual account state rather than claiming every group already exists or has a specific retention policy.

Capture declares one DLQ alarm: AWS/SQS `ApproximateNumberOfMessagesVisible`, queue-name dimension, Maximum over 60 seconds, one evaluation period, threshold greater than zero, missing data `notBreaching`. No alarm action destination is declared. An alarm state alone does not prove an operator receives notification.

## 2. Sections and curated controls

| Section/property | Proposed exposure | Risk/constraint |
|---|---|---|
| Application settings: diagnostic detail | Declared runtime behavior only if a consumer exists | Security-sensitive; avoid identity/evidence payloads |
| Application settings: redaction policy | Security-controlled schema and code support | Cannot recover data already disclosed |
| Artifact settings: log retention | Approved per-group retention values after data classification | Shortening can irreversibly delete records |
| Artifact settings: alarm threshold/window | Bounded DLQ controls with preserved queue/metric | Can hide operational failure |
| Artifact settings: missing-data treatment | Advanced explicit choice | Lack of data is not proof of health |
| Artifact settings: approved notification topic | Later provisioned/verified destination | May disclose operational information |
| Artifact settings: log format/filter level | Lambda-linked capability after runtime verification | Can suppress evidence and diagnostics |
| Artifact settings: subscriptions, encryption, access | Read-only initially; deployment capability | Data export, key/access and delivery disruption |

Category and risk are independent. A diagnostic application setting needs its own sensitive permission. Selecting its source/reader, configuring native retention or changing AWS access belongs in Artifact settings. Do not disguise native alarm configuration as an AppConfig flag.

Show environment/shared scope, account/region, logical function, actual log-group name/ARN and alarm ARN, resource existence, effective settings, desired/applied revision, ownership and drift. Shared administrator logs need separate scope. A selected function version does not imply a private log group or a version-specific retention boundary.

## 3. Retention and logging prerequisites

Classify authentication/security audit records separately from routine diagnostics and identity-card processing metadata. Set retention based on purpose and applicable organizational requirements; do not make every log group inherit the evidence-bucket lifecycle or an arbitrary cost-saving minimum. Never log passwords, proofs, tokens, raw card images or extracted identifiers in previews, history or diagnostic output.

CloudWatch stores logs indefinitely without a retention policy. Shortening retention can remove historical records; expiration/deletion is not instantaneous. Increasing retention afterward does not recreate deleted events. The panel must preview the affected time range, enforce security-record minimums and label this consequence explicitly. DeleteRetentionPolicy means no expiration, not deleting the log group.

Lambda application-level filtering requires JSON format. For custom runtimes, application output must provide supported JSON level/timestamp fields. Verify every Go logging path and emitted format before exposing a filter control; changing a Lambda field alone does not establish meaningful application filtering. Retain essential security events independently of an operator's diagnostic verbosity choice.

## 4. Source, reader and scoped writer

The future managed registry declares typed retention/alarm properties and trusted resource bindings. A native reader describes log groups, alarms and Lambda logging configuration. Approved writers use PutRetentionPolicy and carefully reconstructed PutMetricAlarm requests; log-format changes use the Lambda adapter. CloudWatch does not poll application configuration stores.

PutMetricAlarm overwrites existing configuration. Preserve metric dimensions, statistic, comparison, action arrays and other supported fields while changing only allowlisted properties. Reject unknown critical fields. Do not permit arbitrary alarm action ARNs, metric queries, cross-account links or log subscription destinations.

Give humans separate monitoring-read, retention-write and alarm-configure capabilities by target. Worker IAM is scoped to registered log groups/alarms; describe APIs requiring broader resource access still need backend result filtering. Do not grant DeleteLogGroup, DeleteLogStream, arbitrary data export or notification-publish permissions to ordinary settings jobs. The browser receives no AWS credentials; log-content access is separately authorized from configuration inspection.

## 5. Durable workflow and recovery

Submit a durable job with expected managed revision and observed fingerprint; acquire the affected-resource lease, authorize the diff, apply, read back and record per-resource status. Fingerprints do not provide native atomicity. Coordinate Pulumi deployments through the same authority: currently unmanaged log groups require an explicit ownership/import decision before retention management, while the declared alarm must consume the new desired record or remain deployment-controlled.

For multi-group changes, keep each success/failure visible and resume idempotently. An alarm update and topic-policy/subscription readiness are not atomic. Mark notification delivery unverified until independently checked. Restoration is a new validated update preserving intervening changes; it cannot restore expired logs or retract notifications. Keep group deletion, purge, alarm state forcing and production notification tests outside a settings save.

## 6. Delivery and checks

First inventory resource existence, permissions, retention gaps and notification coverage. Next implement retention with irreversible-impact preview and bounded alarm tuning. Add verified notification bindings and JSON filtering only after their dependencies exist.

Use local/mock checks for complete alarm preservation, missing groups, retention minimums, denied log-content access, cross-environment/shared isolation, stale revisions, external drift, partial batch failure and deployment preservation. Later controlled checks separately verify native state, emitted custom-runtime log filtering and approved test-notification delivery. This document performs none of those cloud operations.

## 7. Provider references

- [Log groups and retention behavior](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html)
- [DeleteRetentionPolicy](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_DeleteRetentionPolicy.html)
- [Lambda log groups and permissions](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html)
- [Custom-runtime log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)
- [PutMetricAlarm overwrite behavior](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricAlarm.html)
