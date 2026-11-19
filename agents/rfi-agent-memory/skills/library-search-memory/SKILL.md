---
name: library-search-memory
description: Search PulsePoint's approved RFI answer library, a read-only memory store under /mnt/memory, for prior answers to a client question. Use whenever the rfi-system-helper-memory skill needs to retrieve answers for a green or amber question.
---

# Library search (memory store)

The library is a read-only memory store mounted under `/mnt/memory/`. Run `ls /mnt/memory/` once to find the store's folder, called `<store>` below.

Each record is one file, `<store>/<stack>/<record id>.md`:

```
id: loopio-13131320
question: How does PulsePoint maintain HIPAA compliance?
stack: Client Strategy- Cleaned
updated: 2025-...
tags: ...
source: loopio

<answer text>
```

## Search

1. **Find candidates.** Grep case-insensitively for 2–4 distinctive terms from the client's question, in alternation:
   ```
   grep -rliE 'hipaa|de-identif|phi' /mnt/memory/<store>/ | head -40
   ```
   To narrow a long list, chain greps, for example `grep -rliE 'ctv|connected tv' … | xargs grep -liE 'frequency|cap'`.
2. **Try other words.** Re-search with the library's likely vocabulary, synonyms, abbreviations and singular/plural forms. Client wording and library wording often differ ("log-level data export" vs "log level reporting").
3. **Read the candidates.** Print the question lines first to shortlist: `grep -h '^question:' $(…list…)`. Then `cat` the best files in full. Read at least the 3 most responsive.
4. **Pick the newest.** When the same question appears in several stacks, the latest `updated` wins. On a tie, prefer `client-strategy-cleaned` or `rfi-2026` over `client-strategy`. Flag anything from `rfi-q-a-bank-v2-unverified` as needing SME confirmation.

If at least three different searches turn up nothing that answers the question, the library has no basis for it. Say so; never stretch an adjacent record.

For each record you use, report its `id`, `question`, `stack` and `updated`.

## Rules

- Read-only: never write, move or delete anything under `/mnt/memory/`.
- If `/mnt/memory/` is missing or empty, the session started without the store. Report it and stop. Never answer from memory in place of a search.
