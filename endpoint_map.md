# endpoint_map.md — api.openai.com endpoint inventory (from developers.openai.com/api/reference, 2026-10-22)

## Administration (org-scope, session-token authz surface)
- GET/POST /v1/organization/admin_api_keys ; GET/DELETE /{id} (admin keys)
- GET /v1/organization/audit_logs
- GET/POST/UPDATE/DELETE /v1/organization/certificates ; /activate ; /deactivate
- GET/UPDATE /v1/organization/data_retention
- GET/POST/DELETE /v1/organization/external_storage ; /validate  [SSRF candidate]
- GET/POST/UPDATE/DELETE /v1/organization/groups ; /groups/{id}/users ; /groups/{id}/roles
- GET/POST/DELETE /v1/organization/invites
- GET/POST/UPDATE /v1/organization/projects ; /archive
  - /projects/{id}/api_keys (GET list/retrieve, UPDATE, DELETE)
  - /projects/{id}/certificates ; /activate ; /deactivate
  - /projects/{id}/data_retention
  - /projects/{id}/groups (+roles)
  - /projects/{id}/hosted_tool_permissions (GET/UPDATE) [NEW]
  - /projects/{id}/model_permissions (GET/UPDATE/DELETE) [NEW]
  - /projects/{id}/rate_limits (GET list, UPDATE)
  - /projects/{id}/roles (CRUD)
  - /projects/{id}/service_accounts (CRUD + api_keys)
  - /projects/{id}/spend_alerts ; /spend_limit
  - /projects/{id}/users (CRUD + roles)
- GET/POST/UPDATE/DELETE /v1/organization/roles
- GET/POST/UPDATE/DELETE /v1/organization/spend_alerts ; /spend_limit
- GET /v1/organization/usage/{audio_speeches,audio_transcriptions,code_interpreter_sessions,completions,costs,decisions,embeddings,file_search_calls,images,moderations,vector_stores,web_search_calls}
- GET/UPDATE/DELETE /v1/organization/users ; /users/{id}/roles
- GET /v1/me [session identity], GET /v1/organizations

## NEW API surfaces (least hardened)
- Agents: /v1/agents CRUD; /v1/agents/environments (+files, templates); /v1/agents/sessions (+artifacts, events, items, subagents); traces/turns
- Vaults (SECRETS): /v1/vaults CRUD; /v1/vaults/{id}/credentials CRUD  [P1 if cross-project/cross-org read]
- Skills: /v1/skills CRUD; /v1/skills/{id}/versions (+content)
- ChatKit: /v1/chatkit/sessions (create/cancel); /v1/chatkit/threads (retrieve/delete/list/items)
- Containers: /v1/containers CRUD; /containers/{id}/files (+content)
- Live: session create/accept/fork/hangup/refer/reject; recording download
- Realtime: /v1/realtime/calls (+accept/hangup/refer/reject); client_secrets
- Webhooks (mgmt NOT in public ref — dashboard-only): create/list/get/update/delete/rotate_secret/TEST
  - Event types: response.*, batch.*, fine_tuning.job.*, eval.run.*, realtime.call.incoming, live.call.incoming, live.transport.incoming, safety.*
- Decisions (beta): dashboard /decisions page; usage under /v1/organization/usage/decisions
- Content Provenance Checks; Safety Alerts (/retrieve, cases)
- Workload identity federation: short-lived access tokens [authz confusion candidate]
- Evals: /v1/evals CRUD + runs; Fine-tuning: jobs/checkpoints/permissions/alpha graders (run/validate)
- Files, Uploads (+parts/complete), Batches, Models, Moderations, Images (gen/edit/variation + streaming)
- Responses: /v1/responses (+input_items, compact, cancel, connect), Conversations (+items)
- Multi-agent Responses (beta): create/retrieve/delete/cancel/compact/connect/input_items/input_tokens
- Chat Completions: (+retrieve/update/delete/list)
- Vector Stores (+file_batches, files, search)

## Legacy dashboard paths (historical, verify alive)
- /dashboard/onboarding/login, /dashboard/user/api_keys, /dashboard/billing/*, /dashboard/usage

## Auth model
- Bearer: sk-... (API key), sk-admin-... (admin key), sess-... (platform session), OR short-lived workload token
- Headers: OpenAI-Organization: org-XXX, OpenAI-Project: proj_XXX
- Session tokens (sess-) accepted by platform UI against api.openai.com/v1/*
- x-request-id in all responses; openai-organization echo header
