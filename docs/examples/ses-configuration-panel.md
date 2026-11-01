# SES custom configuration panel

## 1. Status and current source

This is a proposed panel/adapter plan, not deployed functionality. Follow the [configuration and administration policy](../configuration-and-administration.md): applications own configuration and their custom panels by default; optional standalone feature panels are suppressed under application ownership. Both call the same validated backend.

At [commit 4607807, application infrastructure](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), `senderDomain` provisions SES DomainIdentity and DomainDkim. Optional Route 53 records publish domain verification and three DKIM CNAMEs. `senderAddress` must belong to that domain. The application Cognito pool uses DEVELOPER email configuration with the identity ARN and FromEmailAddress. Signup/resend roles permit SendEmail on SES identities in the selected account/region, constrained by `ses:FromAddress`; the source explains the sandbox recipient-identity requirement.

[Bootstrap](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/cmd/internal/bootstrap/service.go) reads `SENDER_ADDRESS` and creates an SESv2-backed sender. [Email service](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/email/service.go) calls the sender for confirmation links. This uses workload credentials, not SMTP keys. Do not invent an SMTP password rotation control or claim native SES templates are already the source of application messages.

## 2. Sections and useful controls

| Section/property | Proposed exposure | Independent risk |
|---|---|---|
| Application settings: subject/body/localization | Later declared template schema and renderer | Phishing, disclosure, broken verification links |
| Application settings: proof expiry/resend limits | Existing application security policy, where supported | Abuse and account-access security |
| Artifact settings: verified identity/DKIM status | First increment read-only | Account/region-specific operating dependency |
| Artifact settings: approved sender address | Coordinated deployment change | Coupled IAM, Lambda and Cognito delivery |
| Artifact settings: identity/domain replacement | Migration workflow, not text editing | DNS ownership and email outage |
| Artifact settings: sending/account quota status | Read-only account/region view | Shared scope across applications |
| Artifact settings: configuration set/MAIL FROM | Later explicit capability | Reputation, DNS, events and policy dependencies |

Classify behavior by meaning, regardless of storage. Application message wording remains application configuration even if packaged with code; its reader/source binding is artifact configuration. Security-sensitive template and proof changes need stronger property permissions than ordinary content edits. Neither grants SES or IAM management rights.

Show account, region, environment/shared scope, identity ARN/domain, effective sender, DKIM/verification state, Cognito consumers, active Lambda consumers, desired/applied revision, ownership and drift. Account production status is shared regional state; an environment tab cannot imply exclusive ownership.

## 3. Verification and template boundaries

SES identities and sandbox status are regional. Verified sending identity, IAM permission, available quota and recipient eligibility are distinct checks. Production access is an AWS approval process, not an automatic panel toggle. Do not promise a successful access request or silently switch regions to bypass restrictions.

DNS publication is not completed verification. Poll observed SES identity and DKIM state with a deadline and resumable pending status. Keep existing verified identity active during migration. DKIM signing should remain enabled; changing signing method or DNS can temporarily impair authentication. Identity verification tokens and public DKIM records are not secret credentials, but configuration responses still need target authorization.

A future template editor must preserve required link/token placeholders, approved HTTPS origin, escaping, generic anti-enumeration behavior and plain-text/HTML consistency. Native Cognito messages, application-generated verification messages and SES stored templates are different consumers. Identify exactly which renderer supports an edit; do not copy one template into every layer or send email as a side effect of saving.

## 4. Source, adapter and permissions

Use a managed desired record for approved sender values and trusted deployment bindings for identities, roles, pools and functions. Native readers inspect identity/DKIM/account state and consumer configuration. Native/deployment writers coordinate SES, DNS, IAM, Cognito and Lambda adapters; SES does not consume AppConfig automatically. Template runtime sources require an actual compatible reader and declared freshness policy before becoming editable.

A sender migration must validate domain membership and verified regional identity, plan the narrowly bounded IAM FromAddress transition, update every sender consumer and Cognito configuration, verify effective delivery paths, then remove obsolete permission. Preserve unrelated role-policy statements, complete Lambda environment maps and Cognito pool fields. Broadened temporary authority needs explicit bounds and cleanup tracking, never unrestricted FromAddress access.

Separate content-editor, sender-operator and shared-account permissions. Scope worker identity/DNS/IAM mutations to registered resources and exact allowed fields. Broad account-read actions still need backend filtering. The browser receives no AWS credentials. No IAM users/access keys, arbitrary recipients, identity deletion, suppression-list removal or unrestricted send capability belongs to ordinary settings administration.

## 5. Jobs, drift and recovery

Submit a durable change job with expected revision, observed fingerprints, affected consumers and per-step verification. Serialize the identity/consumer set; compare source state before every dependent step. Native APIs do not create a cross-service transaction or universal compare-and-swap. Verification may remain pending while DNS propagates.

Pulumi currently owns sender/DNS/IAM/Cognito/environment declarations. Route changes through deployment initially; a later live adapter requires explicit field ownership and a registry read by subsequent deployments. Do not allow competing writers or stale constants to revert a panel change.

Record partial IAM/Lambda/Cognito progress and stop on failed dependencies. Recovery revalidates the previous verified identity and restores only owned fields. It cannot retract sent email, recover a clicked link, undo reputation damage or promise immediate DNS convergence. Test messages require an independently authorized controlled recipient or SES simulator workflow, never a production-user blast.

## 6. Delivery and checks

Start with identity, quota, sender and consumer inspection. Add coordinated same-domain sender changes before domain migrations. Add templates only after implementing the renderer/schema. Verify permission isolation, regional sandbox handling, expired revisions, complete-map preservation, DKIM pending/failure, partial consumer rollout and deployment reconciliation locally. Later controlled tests distinguish native read-back from actual delivery and verification-link behavior.

## 7. Provider references

- [Verified identities](https://docs.aws.amazon.com/ses/latest/dg/verify-addresses-and-domains.html)
- [Regional sandbox and production access](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)
- [SES IAM and From address controls](https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html)
- [Easy DKIM and DNS dependencies](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html)
- [Cognito email configuration](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-email.html)
