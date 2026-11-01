# CloudFront: post-deployment configuration and custom-panel plan

## 1. Scope and current edge boundary

Reviewed Attestra commit [4607807](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/assetlinks.go) on 2026-11-01. This proposes an Android association panel; no resources change. Follow the [configuration policy](../configuration-and-administration.md).

CloudFront currently serves only public Android Digital Asset Links from a private S3 bucket. It is not the administrator UI CDN and does not front the authentication API. The shared admin UI is served through its existing [API Gateway/Lambda infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go).

| Current setting | Source-derived value |
|---|---|
| Trigger | androidAssociations configured; empty array renders a revocation file |
| Object | .well-known/assetlinks.json, application/json, Cache-Control no-store |
| Origin | Regional S3 endpoint; public access blocked; BucketOwnerEnforced; AES256 |
| Access | OAC, always SigV4 signing; bucket permits only association object for distribution SourceArn |
| Viewer | HTTPS-only; GET/HEAD; SNI certificate in us-east-1; TLSv1.2_2021 |
| Distribution | PriceClass_100; no geo restriction; WaitForDeployment true |
| Cache policy | Managed CachingDisabled, ID 4135ea2d-6df8-44a3-9df3-4b5a84be39ad |

Evidence: [association infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/assetlinks.go) and [configuration gate](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go). Missing configuration is described by source as preserving existing sites; model it separately from an explicit empty array. Inspect the Pulumi plan before treating omission as a guaranteed no-op.

## 2. Two dashboard sections

### Application settings

Approved Android package names and signing-certificate fingerprints express which apps the product associates with the website. Treat those as security-sensitive application settings with explicit association-management permission. They are public identifiers, but unauthorized changes can redirect trust. Validate their schema and supported relation; never request Android signing private keys.

### Artifact settings

Show account/environment, domain alias, distribution ID/ARN, bucket/object binding, certificate region, OAC, deployed status, policy IDs, revision, owner and drift. Cost/coverage and TLS/cache delivery controls belong here. Category and risk are independent: package association edits can be high-risk app changes; read-only distribution inspection is a lower-risk artifact capability.

## 3. Curated post-deployment exposure

| Property/operation | Proposed treatment |
|---|---|
| Distribution/content readiness and ownership | Read-only first increment |
| Publish approved association document | Validated app operation delivered by restricted object adapter |
| Price class | Advanced artifact edit; cost/geographic latency preview |
| Stronger supported TLS baseline | Compatibility-reviewed artifact update; no baseline weakening |
| Reconcile managed cache policy | Restore approved disabled-caching baseline only |
| Invalidation | Restricted recovery operation when justified, not instant trust revocation |
| Alias/certificate/origin/OAC replacement | Coordinated deployment migration |
| General cache behaviors/auth API origin | Not exposed by this panel |

Do not introduce authentication responses, tokens, user-specific bootstrap data or administrator HTML into this association distribution. Any future CDN for those services needs a separate threat/forwarding/cache design. Preserve disabled caching and no-store: a positive minimum TTL can override no-store headers. Adding Authorization to a cache key is not a sufficient generic privacy strategy.

## 4. Adapter contract and authorization

Declare association.document as a typed application property and edge.price_class as a separately authorized artifact property; include risk, scope, validation and supported writer. Names are pseudocode. The app owns its custom panel by default and suppresses an optional standalone feature panel, while both call the same configuration API.

A trusted registry binds distribution, bucket, exact object key, origin and us-east-1 certificate. Browser requests contain approved logical fields and expected revisions, never arbitrary URLs, buckets or CloudFront JSON. An inspection adapter reads distribution configuration/status and object metadata. A content writer can put only the association object; it cannot alter OAC, bucket policy, distribution origins or IAM. A separate artifact worker gets narrowly scoped distribution updates and read access. Shared-admin permissions do not automatically include these capabilities.

No worker credentials, CloudFront signing keys or S3 secrets reach the browser. Retain public diffs and job history; redact credential-bearing errors. Public association contents do not justify expanding origin access beyond the exact object.

## 5. Durable changes, conflicts and recovery

Prerequisites include an issued matching viewer certificate in us-east-1, DNS authority, verified private origin/OAC access and validated association input. Acquire a coordinator lease and compare expected managed revision and observed content hash. For distribution changes fetch the full configuration/ETag, preserve unrelated fields and submit UpdateDistribution with IfMatch. A stale ETag causes replan; the lease does not exclude external writers.

Persist idempotent job steps for object upload, distribution update, deployment wait, optional invalidation and end-to-end retrieval. Record partial failure and retry safely rather than reissuing unrelated operations. Verify status and exact HTTPS object bytes/content type separately from control-plane success. Direct S3 access must remain denied.

Removing a package/fingerprint should publish the intended replacement document, including an explicit empty array where appropriate. Deleting the object or disabling/deleting the distribution is a different outage-producing operation; devices and intermediaries may retain prior association state. Even disabled edge caching does not prove instant Android revocation. Record downstream verification limits and use separate application enforcement if immediate access denial is required.

Pulumi currently owns content and infrastructure. Keep initial writes deployment-controlled; introducing an object worker requires an explicit ownership handoff and desired content consumed by subsequent deployment. Rollback republishes a previously approved document or restores compatible distribution settings with fresh conflict checks. It cannot erase client caches or undo associations already consumed. Retain old origin/certificate resources until migration verification and recovery windows complete.

## 6. Delivery and checks

Phase inspection first, then association publishing with durable jobs, then bounded edge controls. Test absent versus empty configuration, invalid fingerprints, scope escape, ETag/content conflicts, preservation, partial upload/update failure, retries, cache-policy drift, secret-free errors and Pulumi reconciliation. Controlled checks verify HTTPS headers/bytes, allowed GET/HEAD, denied direct S3 reads and Android association behavior. This is a design only.

## 7. Provider references

- [S3 origins and OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [Managed cache policies](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-cache-policies.html)
- [Cache TTL and origin headers](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html)
- [UpdateDistribution and IfMatch](https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_UpdateDistribution.html)
- [Viewer certificate requirements](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html)
