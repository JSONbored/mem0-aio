# Pull Request

## Summary

- what changed
- why it changed

## Validation

- [ ] `trunk check --show-existing --all` passed locally
- [ ] `pytest tests/unit tests/template` passed locally
- [ ] `pytest tests/integration -m integration` passed locally when runtime or CI behavior changed
- [ ] docs updated if behavior changed
- [ ] XML updated if config surface changed

## Risks

- note any migration, data, or compatibility risk
