# Weaviate Admin Access Request — Loopio RFP Tool

**From:** Maggie Kuo (mkuo@pulsepoint.com)
**To:** BI Infra / Fabric Platform Team
**Re:** Weaviate collection + tenant setup for new Fabric app (loopio-rfp)

---

Hi team,

I'm building a new Fabric app (`loopio-rfp`) that answers RFI/RFP questions using PulsePoint's Loopio knowledge library. The backend is an ADK tool (`fabric.loopio.rfp_search`) that searches a Weaviate collection via hybrid search. I need a few things set up to get it working.

## What I need

1. **A Weaviate tenant ID** for the `loopio-rfp` app
2. **An API key / JWT** with `AUTH_FABRIC_WEAVIATE_ADMIN_SCOPE` + `WEAVIATE_TENANT_<id>` scopes so I can create the collection and seed data
3. **The following env vars** (or confirmation of what they're set to in the bi-fabric deployment):
   - `FABRIC_BI_STUDIO_BASE_URL`
   - `FABRIC_IAP_CLIENT_ID`
   - `BI_FABRIC_SVC_JSON` (I assume this is already configured — just need to confirm the loopio tool can use it)

## What I'm creating

- **Collection name:** `loopio_rfp_library`
- **Properties:**
  - `question` (text, `vector_source: true`)
  - `answer` (text)
  - `stack_name` (text)
  - `tags` (text)
  - `last_updated` (text)
  - `category_name` (text)
  - `source_id` (text)
- **Data:** ~1,600 entries from our Loopio library export (Q&A pairs used for RFI/RFP responses)
- **Access pattern:** Read-only from the ADK tool via the existing `/hybrid` endpoint — no browser-side writes

## Context

- The app repo is `pulsepointinc/loopio-rfp` (Fabric app template, pending deploy)
- The ADK tool PR will go to `pulsepointinc/bi-services` on branch `feat/loopio-rfp-adk-tool`
- I have a seeder script ready that calls the `objects:insert` admin endpoint to batch-load the data
- The tool follows the same pattern as `fabric.kb.search` — calls Weaviate via `iap_call()` from bi-fabric

## Also need

- `BI_INFRA_PAT` token for the `loopio-rfp` app repo (for CI/CD deployment to App Engine)
- Confirmation on whether `LOOPIO_WEAVIATE_TENANT_ID` needs to be added to bi-fabric's App Engine env, or if it's handled differently

Happy to hop on a call if it's easier to walk through. Thanks!

Maggie
