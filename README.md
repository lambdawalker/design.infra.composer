# infra.composer

Compose independently maintained backend features through declared contracts, dependency injection, and Pulumi deployments.

**Status: architecture recorded, with reference implementations.** The initial [Python local prototype](https://github.com/lambdawalker/infra.composer.example) validates and simulates composition. The [Go implementation](https://github.com/lambdawalker/go.infra.composer) also provides native Pulumi integration and the [report-backed teardown/nuke lifecycle](docs/teardown-and-nuke.md). Broader configuration delivery, hosted panels and deployment coordination described here remain proposed unless a section identifies implementation evidence. Examples describe a proposed API unless stated otherwise.

## Design record

- [Architecture](docs/architecture.md): feature composition, declarations, dependency validation, standalone providers, environments, credential memory, and control plane.
- [Configuration and administration](docs/configuration-and-administration.md): property contracts, optional standalone panels, source selection, secure readers, and managed-resource updates.
- [Releases and clients](docs/releases-and-clients.md): concurrent releases, compatibility, routing, client lockdown, and scheduled retirement.
- [Teardown and nuke](docs/teardown-and-nuke.md): all-environment destruction, shared admin/index ordering, persistent reporting, recovery-state/key safeguards, and full/remaining-only checks.
- [Attestra artifact inventory and configuration plan](docs/examples/attestra-configuration-plan.md): source-reviewed application of the configuration rules to Go/AWS authentication, storage, identity, messaging, and operations.
- [Artifact configuration-panel catalog](docs/examples/configuration-panel-catalog.md): all 16 artifact types, including application/artifact settings, custom-panel adapters, permissions, change jobs, ownership and recovery.
- [Implementation roadmap](docs/roadmap.md): additional recommendations, acceptance criteria, unresolved choices, and suggested delivery order.

The documents preserve the conclusions of the initial design discussion. **Agreed** identifies explicit requirements; **recommended** identifies proposed additions; **open** identifies decisions still needed. Inclusion of a recommendation does not mean its detailed implementation was approved.

## Central idea

```python
# Proposed API: declarations only until deploy/materialization.
a = Authentication()
b = EmailValidation()
c = Application(features=[a, b])

b.inject(c.getDeclarationsForB(a))
a.inject(c.getDeclarationsForA(b))

c.deploy(environment="dev")
```

Features A and B do not import each other. Application C selects providers and adapts their contracts. Mutual runtime relationships are permitted; circular resource creation prerequisites are rejected before deployment.

Each feature also has a standalone deployment entry point with permitted default providers, enabling independent input/output testing.

## Scope

The design covers feature infrastructure, dev/QA/prod/custom environments, encrypted deployment memory, retained backend releases, client discovery/update policies, and independently deployed admin/index sites.

This repository stores design, contracts, schemas, and eventually code. Credentials, runtime configuration values, live deployment records, and Pulumi state belong in their designated protected stores, not in source control.

## Resource ownership

Apply the [resource ownership standard](docs/resource-ownership.md) to tags, mutable descriptions and metadata-only inventory, including shared resources and provider limitations. Existing resource identifiers are preserved.
