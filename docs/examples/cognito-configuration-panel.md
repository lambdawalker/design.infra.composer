# Cognito: post-deployment configuration and custom-panel plan

## 1. Scope

Next artifact after the [Lambda](lambda-configuration-panel.md) and [API Gateway](api-gateway-configuration-panel.md) plans: Cognito user pools, app clients and managed login.

Reviewed [go.attestra.aws.auth 4607807](https://github.com/lambdawalker/go.attestra.aws.auth/commit/4607807ab0346f4a38532982889fe2e56954412e) on 2026-11-01. This is a source-based design; no user pool, user, credential or deployment is changed. See [artifact inventory](attestra-configuration-plan.md) and [configuration policy](../configuration-and-administration.md).

Cognito resource settings are applied by management APIs or the deployment adapter. Cognito does not automatically read them from AWS AppConfig, DynamoDB runtime records, or Lambda environment variables.

## 2. Current identity boundaries

| Setting | Application users | Shared administrators |
|---|---|---|
| Pool tier / account creation | Essentials; administrator-created only | Essentials; administrator-created only |
| Pool MFA | OFF | ON, with TOTP and SDK-configured verified-passkey support |
| First factors | PASSWORD, EMAIL_OTP, WEB_AUTHN | PASSWORD plus WEB_AUTHN after setup |
| Password baseline | Minimum 8; character requirements false | Minimum 14; lowercase/uppercase/number/symbol required; temporary password 7 days |
| Passkey user verification | Required | Required; SDK sets MULTI_FACTOR_WITH_USER_VERIFICATION and managed-login relying party |
| Recovery | Administrator-only pool recovery; application has its own email sign-in/recovery flow | Administrator-only; independent operator recovery needed |
| Public app client | No client secret; custom/user/refresh auth; auth session validity 3 minutes | No client secret; authorization-code managed login; approved scopes and callback/logout URLs; user auth |
| Token validity declared | Explicit access/ID/refresh lifetimes omitted; inspect effective values | Access/ID 15 minutes; inspect effective refresh lifetime |
| User-existence errors | Suppressed on app client | Suppressed on app client |

The application pool's native password baseline is not the full onboarding password policy. Runtime application policy supplies additional rules and placement requirements.

Evidence: [application pool/client](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra/main.go), [shared pool/client](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/infra-index/admin.go), [admin SDK setup](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/adminsetup/setup.go), [runtime onboarding schema](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/onboarding.go).

Current admin setup deliberately owns fields the Pulumi provider cannot fully express. The shared pool ignores Pulumi changes to signInPolicy/webAuthnConfiguration; SDK setup preserves pool configuration, sets MFA/passkey requirements, then reads them back. A new panel must preserve that ownership contract.

## 3. Two dashboard sections

### Application settings / authentication

| Property | Current meaning | Proposed exposure |
|---|---|---|
| Passkey enrollment requirement | Required / optional / disabled onboarding step | Keep in existing validated runtime policy |
| Password enrollment requirement and placement | Required / optional / disabled; hidden / with email / after verification | Keep in runtime policy, enforcing consistent combinations |
| App password acceptance rules | Min/max length and allowed/required/disallowed character groups | Security-sensitive app control; validate against native pool constraints |
| ID capture requirement | Required / optional / disabled onboarding step | Keep in onboarding/capture policy, not a Cognito pool toggle |
| User-facing authentication messages | Approved app-level wording | Editable only through declared schema, preserving generic anti-enumeration behavior |

Disabling enrollment does not revoke already registered passwords/passkeys or disable their underlying Cognito sign-in factors. Show that distinction in the UI.

Application settings remain application settings even if their selected source changes. They cannot grant their editor pool/client-management rights. Evidence: [enrollment enforcement](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/signin/enrollment.go) and [onboarding contract](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/runtimeconfig/onboarding.go).

### Artifact settings / Cognito

Show the selected account/region, environment or shared scope, logical pool/client, current effective settings, managed revision and drift status. Do not let an environment selector silently target the shared administrator pool.

## 4. What is worth exposing in Artifact settings

| Property | Operational value | Recommended exposure |
|---|---|---|
| Access/ID token lifetimes | Balance reauthentication/load against token exposure window | First writable increment for application client after compatibility tests; bounded and units explicit |
| Refresh token lifetime | Control duration of renewable sessions | Privileged increment; explain existing-session behavior and migration/revocation separately |
| Authentication challenge/session validity | Tune supported multi-step sign-in envelope | Advanced; validate client timing and AWS range, not email-proof lifetime |
| Native password policy / temporary-password lifetime | Maintain pool security baseline and invitation expiry | Security operator only; preview effective app+pool constraints and administrator impact |
| Approved callback/logout URLs | Add/remove known web application endpoints | Privileged incremental change; exact target client and complete allowlist required |
| Managed-login presentation | Controlled branding/translations supported by current flow | Later low-disruption capability, separate from authentication/security settings |
| MFA methods / required versus optional | Strengthen identity controls where client/factor support exists | Advanced planned migration, not a general on/off switch |
| Allowed first factors / client auth flows | Enable a supported authentication capability | Migration-controlled; must match handlers, clients, MFA and recovery |
| Refresh token rotation / grace policy | Reduce refresh-token reuse exposure | Disabled as a simple toggle until refresh implementation is migrated |
| Account recovery / verification behavior | Manage recovery security and delivery | Security-reviewed migration; current admin-only baseline remains locked initially |
| SES sender/template settings used by Cognito | Maintain approved delivery identity and messages | Linked SES/deployment capability, not arbitrary sender text |
| Threat protection / tier-dependent features | Additional risk controls if compatible and supported | Later explicit tier/region/cost and auth-flow compatibility plan |

Expose a small set of supported properties; not every AWS-editable field is useful or safe for routine administration.

For admin pool settings, begin read-only. Writable admin-client/token/MFA controls require a tested independent operator recovery path and explicit shared-identity permission. A runtime grant manager is not automatically an identity infrastructure operator.

## 5. Important compatibility constraints

### Password rules

The current application policy supports restrictions Cognito's pool policy does not express identically, such as disallowed character groups, maximum length and UI placement. Do not copy the application policy object into UpdateUserPool.

Validate the effective set of passwords acceptable to both layers and reject impossible combinations. Preserve enrollment and existing-credential behavior. Do not imply that editing a policy retroactively revalidates every existing password, forces password changes, or revokes sessions; those would require separate explicit operations.

### MFA and passkeys

The application currently permits email OTP as a first factor with MFA OFF. AWS disallows that first-factor combination with required MFA. A direct OFF-to-ON edit can therefore be incompatible.

The shared admin supports required MFA with user-verified passkeys through FactorConfiguration=MULTI_FACTOR_WITH_USER_VERIFICATION, configured by the existing SDK path. Preserve required user verification and TOTP recovery availability; do not weaken the baseline to make a provider update succeed.

A migration must check tier/region support, enrolled factors, client challenge handling, recoverability, SDK/provider field support and read-back. Individual user MFA preferences and passkey enrollment are user security operations, not global pool configuration.

### Refresh tokens and session enforcement

[Current refresh handler](https://github.com/lambdawalker/go.attestra.aws.auth/blob/4607807ab0346f4a38532982889fe2e56954412e/signin/service.go) uses InitiateAuth with REFRESH_TOKEN_AUTH. AWS refresh-token rotation is incompatible with that flow. Enabling rotation requires a compatible refresh API implementation, token-storage/concurrency/retry handling, and rollout across supported clients/backends first.

Token lifetime changes affect issuance policy; they are not an instant "log everyone out" mechanism. Offline JWT signature/expiry verification does not by itself enforce Cognito token revocation. If immediate revocation is required, design and test enforcement at every relevant resource/API boundary; do not infer it from a successful Cognito revoke call.

Compare access/ID/refresh lifetimes with the client refresh strategy, admin session behavior and update policy. Preserve explicit units rather than treating every numeric field as minutes.

### Origins and relying parties

A callback/logout URL edit is not a CORS edit and does not migrate passkey relying-party credentials. Require approved exact HTTPS URLs for the current web admin; native/custom redirect schemes need a separate client-specific policy.

Changing managed-login/custom domains, relying-party IDs, issuers, pool/client identity or audience is a coordinated migration involving existing passkeys, clients, API authorizers, DNS/certificates and bootstrap documents. These remain outside routine editing.

## 6. Not routine configuration

Keep these read-only or link to an explicit deployment/migration operation:

- User pool/client IDs, username/sign-in attribute model, case sensitivity and required/custom attribute schema where immutable or migration-sensitive.
- App client secret presence; adding/removing a secret requires a new client. Current browser/native public clients must not receive one.
- Pool replacement/deletion, self-signup enablement, automatic account linking, public recovery changes and weakening user-existence protections.
- Lambda trigger targets/permissions, external identity providers, external-provider credentials, OAuth grants/scopes beyond approved capabilities, and arbitrary endpoints.
- Managed-login domain/RP migrations, client-secret generation and cross-environment identity reassignment.
- Admin grants, invitations, user disable/delete, password reset, factor removal and global sign-out as side effects of a configuration save.

User administration can have a separately authorized "Identity operations" workflow, with target-user checks, audit and impact. Do not put those actions behind an apparently harmless settings update.

## 7. Proposed property/binding contract

```python
identity.configuration.duration(
    "client.access_token_lifetime",
    category="artifact",
    permission="identity.client.configure",
    risk="security",
)

app.configure_artifact(
    identity.application_client,
    properties={
        "client.access_token_lifetime": ManagedResourceProperty(
            adapter="aws.cognito.app_client",
            field="AccessTokenValidity",
            units="minutes",
            initial_value=approved_access_token_minutes,
        ),
    },
)
```

Pseudocode only. Declare the corresponding TokenValidityUnits mapping and complete client-update behavior; do not send a single scalar field alone.

The artifact registry identifies pool/client by trusted deployment bindings, account/region, environment/shared boundary and allowed operations. The browser supplies approved logical fields and expected revision, not an arbitrary pool ID or AWS request body.

Application settings use their existing runtime adapter; Cognito artifact properties use the native adapter. An application's custom panel owns configuration by default and suppresses a feature's standalone panel while preserving the required identity/configuration services.

## 8. Custom-panel workflow

1. **Inspect:** show effective app policy versus native pool/client policy in clearly separated views; mark shared administrator resources prominently.
2. **Choose property:** only approved typed controls; unsupported/migration-only fields remain read-only with explanation.
3. **Compatibility preview:** list affected clients/releases, factors, callbacks, token/session behavior and coordinated resource changes.
4. **Review exact diff:** identify whether the change affects one app client, the whole user pool, or shared administrators across applications/environments.
5. **Submit durable job:** verify permission, target binding, desired revision and observed-state fingerprint.
6. **Apply through scoped worker:** preserve unrelated settings, honor SDK/Pulumi field owners and record each step.
7. **Verify:** describe/read back pool/client/MFA state; use controlled sign-in checks separately to verify the data plane.
8. **History/recovery:** retain nonsecret before/after values and operation status. Restoration is a new validated operation, not blind replay of an old full resource document.

No automatic production test-account invitation, email, user reset, factor deletion or global logout is part of saving settings. Future smoke checks need controlled accounts and separately authorized operations.

## 9. Safe native update adapter

AWS explicitly warns that omitted UpdateUserPool/UpdateUserPoolClient parameters can reset to defaults. The worker must not issue a one-field update from a generic form.

Required algorithm:

1. Resolve/authorize the target and acquire the coordinator's per-pool/client lease.
2. Read current pool/client settings and MFA configuration as needed.
3. Compare expected registry revision and a normalized fingerprint of managed/current relevant fields; detect changes from other operators/deployments.
4. Convert describe output into a **supported update request**, filtering read-only fields and preserving all applicable updateable settings. Do not assume copying response JSON is universally safe across provider versions.
5. Apply only the approved field changes to that preserved request; validate tier/factor/flow/password/callback dependencies.
6. Coordinate UpdateUserPool, UpdateUserPoolClient, SetUserPoolMfaConfig or branding operations as required by the property. They are not a single atomic transaction.
7. Read back each result and check security invariants; persist applied revision or partial-failure state.
8. Stop on unknown/unrepresentable security-critical fields instead of silently defaulting or lowering security.

Internal revision/fingerprint checks do not create a native AWS compare-and-swap guarantee. External writers may race; detect drift and preserve a conflict-aware recovery path.

Before enabling mutable fields, establish one authority for them. The managed registry feeds both the panel worker and subsequent deployment resolution. Preserve the existing SDK-owned admin passkey/sign-in split. Do not add a blanket ignore over all Cognito settings or let Pulumi overwrite approved changes with old constants.

Rollback cannot restore removed credentials, retract issued tokens, undo notifications, or recreate user state automatically. Revalidate the former settings against current factors/clients before restoration. Pool-wide changes affect all retained backend releases using that pool even when only one client or app release is selected in the dashboard.

## 10. Permissions and secrets

| Actor | Authority |
|---|---|
| Application-settings editor | Approved onboarding/runtime properties in granted environments |
| Identity configuration operator | Explicit pool/client settings capability for selected artifact boundaries |
| Shared-admin identity operator | Additional permission for the administrator identity boundary, with independent recovery |
| Configuration worker | Needed describe/update/MFA/branding actions on registered targets only |
| User/account operator | Separately authorized invitations, resets, disable/delete or factor operations |
| Browser | Application session to configuration API; no AWS worker credentials |

Where IAM scopes management to a pool more broadly than one client/property, backend allowlists still enforce the exact client IDs and fields. Do not grant all Cognito administration to the current runtime-config Lambda.

Current public app clients have no secret; pool/client IDs and issuers are identifiers, not passwords. Do not invent a secret where none is needed. Future external IdP/client credentials, if introduced deliberately, require a protected provider and must not appear in public bootstrap/configuration, logs or previews. User passwords/tokens are not retrievable configuration values.

## 11. Delivery sequence and checks

**Increment 1 — inspection and boundaries:** expose observed/native versus app policy, ownership, target scope, supported-property inventory and missing-binding diagnostics. Keep admin artifacts read-only.

**Increment 2 — bounded application-client changes:** token lifetimes and approved existing-flow callback/logout edits where applicable, with full preservation, scoped worker, durable history and deployment reconciliation.

**Increment 3 — password/flow migrations:** effective-policy validation, client compatibility and reversible sequencing; native security changes require explicit operator authority.

**Increment 4 — advanced MFA/rotation/branding:** implement missing reader/client/backend support first, then controlled capabilities. Admin identity writes remain gated on independent recovery verification.

Tests should cover omitted-field preservation, read-only response filtering, unsupported-field handling, units, missing/invalid bindings, application-versus-artifact permissions, environment-versus-shared isolation, expired/stale revisions, source drift, partial MFA/client update failure, callback allowlisting, app/pool password conflicts, required-MFA/OTP incompatibility, refresh-rotation incompatibility, retained-client behavior, no unintended invitations/user actions, token-revocation enforcement boundaries and deployment preservation.

Local unit/mock tests precede any later approved live checks. Verify native read-back and actual managed-login/API behavior separately. No panel/worker or migrations are implemented by this document.

## 12. Provider references

- [Updating pools/clients: preservation and immutable settings](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-updating.html)
- [UpdateUserPoolClient](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_UpdateUserPoolClient.html)
- [MFA and compatible factors](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
- [WebAuthn configuration](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_WebAuthnConfigurationType.html)
- [SetUserPoolMfaConfig](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_SetUserPoolMfaConfig.html)
- [Refresh tokens and rotation](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-refresh-token.html)
- [Token revocation](https://docs.aws.amazon.com/cognito/latest/developerguide/token-revocation.html)
- [Password policy](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-users-passwords.html)
