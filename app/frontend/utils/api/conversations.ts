// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Conversations API service - mirrors backend/controllers/conversations.py
 * Raw API calls without UI concerns (no toasts, no store updates).
 */

// ============================================================================
// User Endpoints
// ============================================================================

/**
 * Create a new support conversation.
 */
export async function createConversation(data: ConversationCreate): Promise<ConversationRead> {
    return useApi().post<ConversationRead>('/conversations', data);
}

/**
 * List current user's conversations.
 */
export async function getConversations(params?: {
    includeClosed?: boolean;
    limit?: number;
    offset?: number;
}): Promise<ConversationListResponse> {
    return useApi().get<ConversationListResponse>('/conversations', {
        include_closed: params?.includeClosed ? true : undefined,
        limit: params?.limit,
        offset: params?.offset,
    });
}

/**
 * Get a specific conversation with messages.
 */
export async function getConversation(conversationId: number): Promise<ConversationDetail> {
    return useApi().get<ConversationDetail>(`/conversations/${conversationId}`);
}

/**
 * Get paginated messages for a conversation.
 */
export async function getMessages(
    conversationId: number,
    params?: {
        limit?: number;
        offset?: number;
        beforeId?: number;
    },
): Promise<MessageListResponse> {
    return useApi().get<MessageListResponse>(`/conversations/${conversationId}/messages`, {
        limit: params?.limit,
        offset: params?.offset,
        before_id: params?.beforeId,
    });
}

/**
 * Send a message in a conversation.
 */
export async function sendMessage(conversationId: number, data: MessageCreate): Promise<MessageRead> {
    return useApi().post<MessageRead>(`/conversations/${conversationId}/messages`, data);
}

// ============================================================================
// Admin Endpoints
// ============================================================================

/**
 * Create a conversation with specific users as participants (admin only).
 */
export async function adminCreateConversation(data: {
    subject: string;
    content: string;
    subtype?: ConversationCreate['subtype'];
    participant_user_ids: number[];
}): Promise<ConversationRead> {
    return useApi().post<ConversationRead>('/admin/conversations', data);
}

/**
 * List all support conversations (admin only).
 */
export async function adminGetConversations(params?: {
    includeClosed?: boolean;
    subtype?: ConversationCreate['subtype'];
    limit?: number;
    offset?: number;
}): Promise<ConversationListResponse> {
    return useApi().get<ConversationListResponse>('/admin/conversations', {
        include_closed: params?.includeClosed ? true : undefined,
        subtype: params?.subtype,
        limit: params?.limit,
        offset: params?.offset,
    });
}

/**
 * Get any conversation by ID (admin only).
 */
export async function adminGetConversation(conversationId: number): Promise<ConversationDetail> {
    return useApi().get<ConversationDetail>(`/admin/conversations/${conversationId}`);
}

/**
 * Update a conversation (admin only).
 */
export async function adminUpdateConversation(
    conversationId: number,
    data: { is_closed?: boolean },
): Promise<ConversationRead> {
    return useApi().patch<ConversationRead>(`/admin/conversations/${conversationId}`, data);
}

/**
 * Send an admin reply to a conversation.
 */
export async function adminSendMessage(conversationId: number, data: MessageCreate): Promise<MessageRead> {
    return useApi().post<MessageRead>(`/admin/conversations/${conversationId}/messages`, data);
}
