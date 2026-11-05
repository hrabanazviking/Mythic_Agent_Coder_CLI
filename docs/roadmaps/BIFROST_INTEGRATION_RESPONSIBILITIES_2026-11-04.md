# Mythic Agent CLI: Bifröst Project Registry and Research Client

**Date:** 2026-11-04  
**Repository:** `hrabanazviking/Mythic_Agent_Coder_CLI`  
**Status:** Design tasks only, no implementation changes.

## Sources of authority

- [Canonical 10,357-word master roadmap](https://github.com/hrabanazviking/bifrost-viewer/blob/main/docs/roadmaps/BIFROST_SECOND_BRAIN_MASTER_EXPANSION_ROADMAP_2026-11-04.md)
- [Full local roadmap copy](BIFROST_SECOND_BRAIN_MASTER_EXPANSION_ROADMAP_2026-11-04.md)
- Existing project source/architecture/compatibility tests. Do not mistake roadmap proposals for implemented behavior.

## Mission

Give the coding-agent CLI optional access to project decisions and research stored in Bifröst without giving it uncontrolled management of every repository.

## This repository's implementation work

1. Use a scoped authenticated Bifröst REST/MCP research client, never raw PostgreSQL.
2. Query source-cited documentation, architectural history, past decisions and selected project status.
3. Publish verified progress summaries only through a separate optional project-write capability.
4. Track event IDs, commit SHAs, and acceptance gates to avoid invented progress and duplicated work.
5. Let users choose which repositories and projects are visible, including an offline mode.
6. Do not send secret-filled local configs, Git credentials or Kista material into the Second Brain corpus.
7. Honor read-only permission by default; explicit owner decision before writing tasks or notes.

## Acceptance gates

- [ ] No unapproved project modifications
- [ ] Agent status is evidence-linked
- [ ] Works offline with integration disabled

## Mandatory safety boundaries

- Keep project behavior, original data, and tested APIs unchanged unless an explicitly approved migration is staged, benchmarked and reversible.
- The Bifröst Viewer server owns the knowledge API, Ingest owns source writes, Skein owns derived graphs, and Skry remains read-only.
- All integrations must be optional, independently authenticated, scoped and resilient to server outages.
- Never commit live credentials, Google OAuth tokens/client secrets, API keys, Kista vault values, personal account information, downloaded private documents, full DB dumps, or runtime logs.
- Use sanitized fixtures and error/credential canary tests. Public descriptions of integrations are not claims of working connections.

## First safe engineering step

Inventory the existing implementation and any newer unpublished local work, then write a small versioned integration interface and associated synthetic tests. Maintain independent project development and review operational changes before deployment.
