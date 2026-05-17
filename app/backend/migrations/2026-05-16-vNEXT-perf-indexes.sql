-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
--
-- Performance indexes. Each addresses a hot-path seq-scan or sort:
--
--   idx_users_stripe_id          — Stripe webhooks resolve users by stripe_id
--                                  (controllers/stripe.py::_apply_user_premium).
--                                  Without this, every webhook is a seq scan on
--                                  the users table.
--
--   idx_messages_conv_created    — conversation list/detail orders messages
--                                  by created_at DESC within a conversation
--                                  (crud/conversations.py::get_last_message,
--                                  get_messages). Composite avoids the sort.

CREATE INDEX IF NOT EXISTS idx_users_stripe_id
    ON users (stripe_id)
    WHERE stripe_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_conv_created
    ON messages (conversation_id, created_at DESC);
