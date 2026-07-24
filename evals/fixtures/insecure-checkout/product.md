# Checkout prototype

This local prototype claims to let signed-in users buy a plan and view only their own paid orders.

The checkout client sends a `user_id`, `sku`, and an idempotency key to `POST /api/checkout`. The order screen reads `GET /api/orders`. It is intended only for local evaluation and must bind to `127.0.0.1`.
