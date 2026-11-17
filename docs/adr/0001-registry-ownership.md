# ADR 0001 Itonami registry ownership

Status: accepted for initial publication, 2026-10-10.

## Decision

cloud-itonami/app-itonami-itonami-registry owns curated, reusable bot role templates, operational skills, workflow recipes and MCP connection definitions. Hermes storage shapes are preserved; Itonami parameter, effect, authority and provider discovery data use separately versioned schemas.

Actual profiles remain under hermes/profiles in their existing repositories. Source relationships express derivation, not adoption. Templates grant no capabilities, inherit no bot identity, import no prior measurements, and activate no cron. A target owner binds a new definition and its existing policy in the target repository.

kotoba-lang/kotoba-registry owns the Kotoba extension catalog. Shared forest maintenance entries are immutable external references. Runtime implementations, capability admission, west registration/pins and application credentials retain their current owners. Publication does not imply west registration, client integration, deployment or live qualification.

## Initial scope

Six curated entries: two role templates, one cron skill, two workflow recipes and the murakumo-web connection. Two physical-AI parameter examples and eleven provider-qualified tool references support agent discovery. The MCP implementation is referenced, not copied. Profiles are paraphrased into generalized templates; source file hashes retain provenance.

## Compatibility

Hermes schemas are vendored from one pinned upstream commit with MIT attribution. No fifth manifest type is introduced. Profile scaffolds are attached to agent entries; tool contracts are a supplemental provider index. Wildcard version filters are not runtime qualification. Workflows are Itonami recipes until an executor is separately qualified. Federation and template binding require consumers; index publication alone changes no installed agent.
