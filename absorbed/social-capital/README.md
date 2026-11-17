# ao-social-capital

`cloud-itonami/ao-social-capital` — resident bot for the social-capital measurement.

The social-capital bot. Its SOUL names kotoba-lang/social-capital, which does not exist; this repository is its home until that library does.

The subject and the bots are one repository: the Hermes profiles that act
here live in [`hermes/profiles/`](hermes/) and are the source of truth for
`~/.hermes/profiles/<profile>` on the host (ADR-2609241200). Secrets, ledgers,
workspace and run state stay on the host.

## Naming

`ao-` is the role prefix for a repository that is a resident bot (the
kotoba-lang/ao artificial-organism model) whose subject and Hermes profile
live together. Identity is the path `cloud-itonami/ao-social-capital`.

## Profiles

| profile | role |
|---|---|
| `social-capital` | social-capital: propose-only bot for the individual data contribution social capital ledger. Measures hyakka claims, aozora records, yataver |
