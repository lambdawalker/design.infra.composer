# IAM and OIDC: post-deployment configuration and custom-panel plan

## 1. Scope and current trust boundaries

Reviewed Attestra commit [4607807](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/aws_setup.go) on 2026-11-01. This proposes restricted administration; no live IAM change occurs. Apply the [configuration policy](../configuration-and-administration.md).

| Boundary | Current source-derived behavior |
|---|---|
| Runtime | Per-handler Lambda execution roles; service trust and workload-specific grants |
| Deployment | GitHub OIDC provider, sts.amazonaws.com audience, exact environment-bound subject |
| Existing deployment role | Ownership/subject tags checked before reuse; managed trust/policies read back |
| Deployment permissions | Broader control-plane grants than runtime; named role patterns; Lambda-only PassRole condition |
| Human administrator login | Separate Cognito managed-login boundary; not GitHub-to-AWS OIDC |

Sources: [setup and subject generation](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/aws_setup.go), [deployment policies](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/aws_setup_policy.go), [runtime roles](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [shared admin identity](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go), [bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/tools/deploy/internal/workflow/bootstrap.go).

Setup uses an ID-bearing subject from 2026-07-16 creation dates. Current GitHub rules also cover opt-ins, renames/transfers; verify actual claims. Current broad provisioning policies are unsuitable for settings workers.

## 2. Two dashboard sections

### Application settings

Business behavior and approved app-level administrator grants remain in their existing application controls. An app administrator's Cognito session can authenticate a request, but backend authorization must independently determine the target/action. An ordinary grant-management permission cannot create an AWS administrator or rewrite deployment trust.

### Artifact settings

Show account, environment/shared scope, registered role/provider ARN, trusted issuer/audience/subject, attached/inline policy inventory, permissions boundary, session limits, owner, revision and drift. Keep policy documents read-only initially. Category and risk are independent: app grants may be security-critical; artifact inventory reads do not imply mutation authority.

## 3. Curated controls

| Capability | Proposed exposure |
|---|---|
| Inspect effective role bindings and trust drift | First read-only increment |
| Revalidate registered role access | Authorized diagnostic job, with stated coverage |
| Select an approved reader/writer role binding | Deployment-coordinated, compatibility checked |
| Bounded session duration | Identity-operator change after workflow checks |
| Change repository/environment subject | Planned identity migration with independent recovery |
| Add wildcard principals, arbitrary actions/resources or raw policy JSON | Never a routine panel control |
| Create access keys or return STS credentials | Not exposed |

Use protected GitHub environments, approved deployment branch/tag rules and reviewers where applicable. Bind OIDC trust to the actual repository/environment subject and correct audience. Environment-bound subjects require environment protection to constrain which workflows reach them. Human AWS operators should use federation/SSO and temporary credentials through a separate operator path; Cognito dashboard login is not automatically AWS operator federation.

## 4. Backend contract and least privilege

Declare role.inspect and identity.binding.migrate as typed artifact capabilities with permission, sensitivity, risk and registered target. The application's custom panel owns configuration by default, suppressing a standalone feature panel while using the same server authorization and adapters.

Resolve logical artifact bindings from a trusted registry; reject arbitrary role ARNs, policy documents, principals and target accounts supplied by the browser. Use separate per-artifact reader and writer roles. Runtime readers get only required source/data reads; configuration workers get only supported property writes on registered targets. Operator/bootstrap privileges remain separate from both. Avoid attaching the broad deployment role to the current runtime-config Lambda.

The worker must not modify its own trust, policies, permissions boundary or role selection. Model escalation paths across iam:PassRole, policy attachment/version changes, trust changes, STS role chaining and Lambda code/configuration updates. Passing a powerful role to attacker-controlled compute can defeat a superficially restricted policy. Bound PassRole to approved role ARNs and service conditions; also constrain the compute operations that consume it. Tags alone are not a reliable PassRole restriction.

Never expose credentials/tokens/private keys in responses or audit diffs. Record public changes, hashes and actors; protect secret references.

## 5. Change jobs, effective checks and recovery

Prerequisites include verified account/repository ownership, protected environment, supported claim format, current trust/policy inventory and an independent tested operator recovery route. Shared identity/deployment changes must not rely on the session or role being changed for their only recovery path.

A durable job authorizes the capability, leases the role, compares revision/fingerprints, preserves unrelated statements/attachments and records steps. Detect out-of-band changes and require replan. IAM does not provide a universal atomic compare-and-swap across trust, policies and bindings; do not claim an internal revision prevents all external races.

Stage a replacement role or additive compatible trust where justified, verify approved workload assumption and least-privilege access, switch the binding, then remove obsolete trust after the recovery window. Additive trust must stay narrowly scoped and time-bounded. IAM propagation can delay successful assumption or enforcement; poll with bounded retries and record pending/partial status.

Read-back proves the stored document, not effective access. Evaluate identity policies, resource policies, boundaries, SCPs, session policies and explicit denies, then use controlled probes where feasible. Policy simulation alone is not proof of all production authorization paths. Removing trust does not necessarily terminate already issued sessions; address active-session revocation separately with explicit impact and verification.

Pulumi owns runtime roles; setup owns deployment trust/policies. Preserve these owners and reconcile proposed desired changes into their next plans. Avoid competing SDK writes or blanket ignored policies. Rollback revalidates previous trust against current ownership and threats; it must not restore a compromised principal merely to regain deployment access.

## 6. Delivery and tests

Deliver inspection first, diagnostic access checks second, approved binding/session changes third, identity migrations last. Test app/operator isolation, environment/shared scope, malicious ARN/policy input, wildcard subject rejection, customized claim mismatches, self-escalation, PassRole abuse, stale revisions, partial writes, propagation retries, denied effective access, independent recovery and deployment preservation. Controlled OIDC probes follow local mocks; no credential or production trust changes occur here.

## 7. Provider references

- [AWS GitHub OIDC trust restrictions](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html)
- [GitHub immutable subjects](https://docs.github.com/en/actions/reference/security/oidc)
- [GitHub OIDC in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [PassRole scope and escalation considerations](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html)
- [IAM security best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Policy evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)
- [Temporary-session revocation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_control-access_disable-perms.html)
