# VASH Catalog

The catalog holds every technology choice VASH can make. A project selects one option per category (stack, LLM, forge, CI, cloud) in its `project-stack.json`.

## Categories

- **Stacks**: The technology pack (e.g., `design-only`, `oracle-apex`).
- **LLM**: The AI models (e.g., `ollama`, `anthropic`).
- **Forge**: The Git host (e.g., `github`, `gitlab`).
- **CI**: The pipeline tool (e.g., `github-actions`, `local-hooks`).
- **Cloud**: The infrastructure host (e.g., `oci-always-free`).

## Skills and agents

- **Skills** (`skills/<name>/SKILL.md`) follow the open Agent Skills standard (agentskills.io): `name`, `description`, `license`, and VASH's own fields under `metadata` (`vash-*`). Every coding tool that reads the standard can use them.
- **Agents** (`agents/<name>.md`) use VASH's neutral format (`method/templates/agent.md`); `vash load` writes them per tool.
- Create with `vash skill new` / `vash agent new` (add `--catalog` for this catalog); check with `vash skill validate` (Gate 1 rule G1-13).
- A project keeps its own skills in its `skills/` and `agents/` folders; a generic one comes here through the catalog-submission form, without client names.

## Adding an Option

**Vendor first (owner rule):** when the vendor of the platform (Oracle, GitHub, Anthropic, ...) provides an equal or better option, the vendor's option is used. A third-party or personal project is chosen only when the vendor has nothing comparable, and the search log says why.

1. Search for the tool (LAW 3): the vendor's own repositories first, then open-source indexes. Document the search in `search-log.md`.
2. Check its licence.
3. Write the catalog entry (with frontmatter).
4. Write the adapter (if it needs code).
5. Submit a PR for AvA review.

Every entry in this catalog is a candidate until the ADR that adopts it is ACCEPTED.
