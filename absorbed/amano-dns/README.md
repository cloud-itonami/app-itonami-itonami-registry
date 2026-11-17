# ao-amano-dns

`cloud-itonami/ao-amano-dns` — resident bot for the amano app-chain dns mesh.

Operates the self-hosted DNS and content-addressed web mesh for the amano app-chain, proposing transactions for amano/dns.

The subject and the bots are one repository: the Hermes profiles that act
here live in [`hermes/profiles/`](hermes/) and are the source of truth for
`~/.hermes/profiles/<profile>` on the host (ADR-2609241200). Secrets, ledgers,
workspace and run state stay on the host.

## Naming

`ao-` is the role prefix for a repository that is a resident bot (the
kotoba-lang/ao artificial-organism model) whose subject and Hermes profile
live together. Identity is the path `cloud-itonami/ao-amano-dns`.

## Profiles

| profile | role |
|---|---|
| `chain-amano-dns` | Self-hosted DNS & Content-Addressed Web mesh operator for amano app-chain. |
