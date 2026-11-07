# BUG-007 (DRAFT): RAG index poisoning — authenticated ingestion of attacker-controlled documents into shared org-wide AI indexes

**Status:** CONFIRMED (ingestion + index-count delta, two document types)
**Severity recommendation:** P3 (P2 if AI consumer surfaces demonstrably render poisoned content to other users)
**Target:** `https://bugbounty1.qe.optrostaging.ai` — `POST /api/v1/rag/add_document`
**Reporter:** zeno0 (token 231), header `X-Optro-Bug-Bounty: zeno0` required.

## Summary

The RAG ingestion endpoint accepts documents from any authenticated user into **shared, org-wide retrieval indexes** used by AuditBoard AI features. An attacker can upload a crafted file through the normal upload flow, then ingest it under a chosen `documentType` (e.g. `knowledge_library`, `tprm_audit_survey_suggestion_contexts`). The document's content is parsed, chunked, embedded, and **permanently added to the shared index** (verified via `rag/index/status` counter deltas). Content is not validated, attributed to a trusted source, or reviewable — a persistent, attacker-controlled retrieval context for AI features that other users consume.

## Evidence (reproduced twice, two index types)

1. Upload chain (normal app flow, replayed via API):
   - `POST /api/v1/files/s3_upload_signature` `{file_name, model_name, model_id, content_hash(MD5, base64)}` → S3 POST policy
   - S3 POST multipart → 201
   - `POST /api/v1/files` `{"file":{...key,url,fileable_id,fileable_type,...}}` → 200, file id (e.g. 2617, 2621)
2. Ingest:
   ```
   POST /api/v1/rag/add_document
   {"documents":[{"fileId":"2617","url":"<presigned S3 URL of file 2617>","documentType":"tprm_audit_survey_suggestion_contexts"}]}
   → 200 {"status":"success","results":[{"fileId":"2617","status":"success","chunks":1}]}
   ```
   `GET /api/v1/rag/index/status` → `totalDocuments` **4680 → 4681**.
3. Second ingest with `documentType:"knowledge_library"` (marker text `KNOWLEDGE-LIB-POISON-MARKER-<ts>` inside the workbook) → 200, chunks:1, counter **4681 → 4682**.
4. Index document types observed live: `policy_published_versions`, `knowledge_library`, `knowledge_library_answers`, `tprm_audit_survey_suggestion_contexts` — all shared, cross-user retrieval namespaces.

`documentType` is a free string parameter on a shared index — the client, not the server, decides which trust namespace a document lands in.

## Session (f)+(g) — consumer hunt + systemic bypass confirmation

**Ingest bypass is systemic (6 of 10 index types demonstrated, same endpoint, zero per-type permission checks):**

| documentType | permission required for the REAL resource | rag/add_document check | result |
|---|---|---|---|
| knowledge_library | — (product module) | none | 200, index +1 (4681→4682) |
| tprm_audit_survey_suggestion_contexts | — | none | 200, index +1 (4680→4681) |
| controls_data | `controls:action.create` (denied for module-less tenants) | **none — bypass** | 200, 390→391 (fake control ZXPOISON-CTRL-7734) |
| framework_items | framework module write | **none — bypass** | 200, 3629→3630 |
| risks | `risk:action.create` | **none — bypass** | 200, 231→232 |
| policy_published_versions | policy module (create DENIED to this account: `policy:action.create`) | **none — bypass** | 200, 0→1 (first-ever doc; fake "published policy" text incl. HTML payload) |

Full enum leaked via `rag/index/status`: `policy_published_versions, knowledge_library, knowledge_library_answers, tprm_audit_survey_suggestion_contexts, controls, controls_data, framework_items, risks, program_regulation_items, auditable_entities`.

**Consumer retrieval hunt — all four AI consumers checked, NONE retrieves poisoned content in QE (honest limitation):**

1. `POST /api/v1/generative/stream` `chain:narrative` — baseline vs poisoned-regeneration diff for narrative 31 (29,633 → 33,437 chars): ZERO marker strings (ZX-TRACK-9Q, webhook.site, `<img`) — the narrative chain does not read these index types.
2. Assistant (`POST /api/v1/assistant/chat/stream`, mode ask) — live-verified: tool `search_knowledge_base` executed server-side but searches the separate admin-managed `assistant_knowledge_files` corpus; poisoned `knowledge_library` chunk NOT retrieved ("I couldn't find that policy..."). Registering a file as assistant knowledge: `POST /api/v1/assistant_knowledge_files` → 403 Forbidden for Owner role (clean authz).
3. `POST /api/v1/ml-recommendations/match-by-id/suggestions` (the ONLY supported pair: id_model `narratives` + match_model `controls_data`) — returns `{}` for all tested narratives (pre-poison too) and a persistent backend failure (`"Failure matching suggestions to id:57..."`) — matcher ML backend degraded/non-functional in QE; poisoned control not retrievable. Score 0.0/0.6/0.9 identical.
4. Agentic TPRM survey suggestions — `audit_surveys` exist but `is_agentic_tprm: false` (feature flag OFF in QE).

**Final severity: P3 stands.** Confirmed: persistent attacker-controlled content in shared AI indexes + ingest path bypasses resource-level permissions (notably `controls:action.create`, `policy:action.create`-gated content). NOT demonstrable in QE: end-user retrieval of poisoned content (all consumers off/gated/degraded) — reported honestly; P2 would require a live consumer demo.

## Impact (stated honestly)

- Any authenticated user can persist arbitrary text into retrieval indexes consumed by AI features for **all org users** (TPRM audit survey suggestions; Knowledge Library Q&A), enabling persistent prompt-injection / misinformation / data-integrity attacks on AI outputs.
- No content provenance: ingested docs appear indistinguishable from legitimately published knowledge.
- **Not demonstrated in QE:** end-user-facing retrieval output (assistant/knowledge QA surfaces are feature-gated in this environment), so consumer-side impact is asserted from architecture, not observed rendering — hence P3 recommendation, upgradeable if a consumer surface is demonstrated.
- SSRF via the `url` parameter is NOT possible: non-S3 URLs (webhook/OAST/IMDS) fail in <0.5s with no outbound callback — URL allowlist enforced. Blind oracle only.

## Reproduction (Burp Repeater)

```
POST /api/v1/rag/add_document HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 231:<secret>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"documents":[{"fileId":"2617","url":"<presigned GET url from GET /api/v1/files/2617>","documentType":"knowledge_library"}]}
```

Prep: upload any .xlsx containing attacker text via the standard upload flow (or create a Narrative and use its file). Then observe `GET /api/v1/rag/index/status` counter increment.

## Remediation suggestions

- Bind document provenance server-side: derive `documentType` and source from the file record/permission model, not client input; restrict ingestion to system flows.
- Add content review/quarantine for user-supplied documents entering shared indexes; label retrievals with source + uploader.
- Rate-limit and audit `rag/add_document`; expose index contents to admins for takedown.

## Session artifacts

- `scripts/t009e_atomic.py` (upload chain), `scripts/t009f_rag_real.py` (ingest matrix), state/t009f_rag.json
- Files created: 2614, 2615, 2617, 2621 (test account, narrative 62)
- Index counter deltas: 4680 → 4681 → 4682
