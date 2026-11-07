# BUG-007 — SUBMISSION DRAFT (Bugcrowd, ready to paste)

**Title:** AI RAG index poisoning: `POST /api/v1/rag/add_document` ingests attacker-controlled documents into shared org-wide AI indexes with no permission or provenance checks (bypasses `controls:action.create` / `policy:action.create` on the ingest path)

**Target:** https://bugbounty1.qe.optrostaging.ai — `POST /api/v1/rag/add_document`

**Requested severity:** P3 (persistent attacker-controlled content in shared AI retrieval indexes + resource-permission bypass on the ingest path; end-user retrieval not demonstrable in this environment — see "Limitations, stated honestly")

**Reporter:** zeno0

---

## Summary

`POST /api/v1/rag/add_document` lets ANY authenticated user inject arbitrary documents into the organization's shared retrieval-augmented-generation (RAG) indexes used by AuditBoard AI features. The caller fully controls the `documentType` trust namespace (a free string validated only against an enum) and supplies a presigned URL to attacker-uploaded content. The document is parsed, chunked, embedded and **permanently persisted into org-wide indexes** — with no permission check against the resource the index represents, no content review, and no provenance/attribution.

Concretely: this account cannot create policies or controls (`policy:action.create` and `project_plan_container:action.create` denied; `controls:action.create` unavailable), yet the same account ingested fake **controls_data**, **framework_items**, **risks**, and **policy_published_versions** documents into their AI indexes via this endpoint — content that claims to be legitimate control/risk/policy data and becomes retrieval context for AI features used by all org users.

## Steps to Reproduce (copy-paste)

1. Upload any .xlsx via the standard upload flow (replayed here via API):

```
POST /api/v1/files/s3_upload_signature HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 231:<redacted>
X-Optro-Bug-Bounty: zeno0
Content-Type: application/json

{"file_name":"poison.xlsx","model_name":"Narrative","model_id":31,"content_hash":"<base64 MD5 of file>"}
```
→ S3 POST policy; upload the file to the returned S3 URL (201); then:
```
POST /api/v1/files
{"file":{"name":"poison.xlsx","fileable_id":31,"fileable_type":"Narrative","creator_user_id":231,"upload_user_id":231,"size":"<size>","type":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","storage_type":"s3","key":"<key from policy>","url":"<location>","user_agent":"AuditBoard/47.1.0","meta":{},"local_folder_path":""}}
```
→ 200, file id.

2. Ingest into a shared AI index (choose any type):

```
POST /api/v1/rag/add_document HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 231:<redacted>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"documents":[{"fileId":"2655","url":"<presigned GET url from GET /api/v1/files/2655>","documentType":"policy_published_versions"}]}
```

→ `200 {"status":"success","message":"Successfully processed 1 document(s)","results":[{"fileId":"2655","status":"success","chunks":1}]}`

3. Verify persistence in the shared index:

```
GET /api/v1/rag/index/status
```

Observed counter deltas (all from this account, Owner test role):

| documentType | delta | note |
|---|---|---|
| tprm_audit_survey_suggestion_contexts | 4680→4681 | TPRM survey suggestion corpus |
| knowledge_library | 4681→4682 | Knowledge Library corpus |
| controls_data | 390→391 | fake control "ZXPOISON-CTRL-7734" |
| framework_items | 3629→3630 | fake framework item |
| risks | 231→232 | fake risk |
| policy_published_versions | 0→1 | first-ever doc in this type; fake "published policy" text |

4. Full index-type enum (leaked via `GET /api/v1/rag/index/status`): `policy_published_versions, knowledge_library, knowledge_library_answers, tprm_audit_survey_suggestion_contexts, controls, controls_data, framework_items, risks, program_regulation_items, auditable_entities`.

## Impact

- **Persistent AI data integrity attack:** any authenticated user can persist arbitrary text as "knowledge", "published policy", "control data", "risk" or "TPRM survey context" inside the org's AI retrieval corpus. Ingested content is indistinguishable from legitimate published knowledge (no provenance, no review), enabling persistent prompt-injection / misinformation against AI features for all org users.
- **Permission bypass on the ingest path:** the endpoint performs no authorization against the underlying resource domain — content the account cannot create in the product (policies, controls — create actions explicitly denied) can still be injected into the AI indexes representing those resources.
- **Persistence:** entries remain in the index until an admin takedown mechanism (not exposed to users) is used.

## Limitations, stated honestly

- In this QE environment none of the four AI consumer surfaces could be shown returning the poisoned content to end users: the narrative generation chain does not read these index types (baseline/poisoned output diff: zero marker strings); the Assistant searches a separate admin-managed corpus (`assistant_knowledge_files`, register denied 403 for Owner — clean); the ML matcher backend (`ml-recommendations/match-by-id/suggestions`) returns no matches/persistent backend failure in QE; agentic TPRM is feature-flagged off (`is_agentic_tprm: false`). Consumer-side impact is therefore asserted from architecture, not observed rendering — hence P3 rather than P2.
- SSRF via the `url` parameter is NOT possible: non-S3 URLs (webhook/OAST/IMDS) are rejected in <0.5s with no outbound callback — an allowlist is enforced on that parameter.

## Remediation suggestions

- Derive `documentType` and document provenance server-side from the file record and permission model; reject client-chosen trust namespaces; gate ingestion behind system flows only.
- Enforce the same resource-level permissions on ingest that the represented domain requires (`controls:action.create`, policy publishing rights, etc.).
- Add content review/quarantine for user-supplied documents entering shared indexes; label retrieval results with source + uploader; expose index contents to admins for takedown.
- Rate-limit and audit `rag/add_document`.
