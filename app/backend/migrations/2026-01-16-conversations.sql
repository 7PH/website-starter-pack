-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add messaging/conversation system
-- Supports support tickets (user-to-admin) and future direct messages (user-to-user)

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,

    -- Conversation metadata
    type VARCHAR(50) NOT NULL DEFAULT 'support',
    subject VARCHAR(255),

    -- Creator (for support: the user who opened the ticket)
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Status
    is_closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(type);
CREATE INDEX IF NOT EXISTS idx_conversations_created_by_id ON conversations(created_by_id);
CREATE INDEX IF NOT EXISTS idx_conversations_is_closed ON conversations(is_closed);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Message content
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,

    -- Admin flag for support conversations
    is_admin_response BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Create conversation participants table (for future direct messages and read tracking)
CREATE TABLE IF NOT EXISTS conversation_participants (
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Read tracking
    last_read_at TIMESTAMPTZ,

    -- Timestamps
    joined_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (conversation_id, user_id)
);

-- Create indexes for participants
CREATE INDEX IF NOT EXISTS idx_conversation_participants_user_id ON conversation_participants(user_id);
