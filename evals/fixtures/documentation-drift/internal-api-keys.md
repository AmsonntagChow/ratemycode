# Internal API-key standard

Applies to the production v1 API.

- Send the key as `Authorization: Bearer <key>`.
- API keys expire 30 days after creation.
- Revoke a key with `DELETE /v1/api-keys/{key_id}`.
- A revoked key stops authorizing new requests immediately.
