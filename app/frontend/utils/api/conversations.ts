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
    const query = new URLSearchParams();
    if (params?.includeClosed) query.set('include_closed', 'true');
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());

    const queryString = query.toString();
    return useApi().get<ConversationListResponse>(`/conversations${queryString ? `?${queryString}` : ''}`);
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
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());
    if (params?.beforeId) query.set('before_id', params.beforeId.toString());

    const queryString = query.toString();
    return useApi().get<MessageListResponse>(
        `/conversations/${conversationId}/messages${queryString ? `?${queryString}` : ''}`,
    );
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
 * List all support conversations (admin only).
 */
export async function adminGetConversations(params?: {
    includeClosed?: boolean;
    limit?: number;
    offset?: number;
}): Promise<ConversationListResponse> {
    const query = new URLSearchParams();
    if (params?.includeClosed) query.set('include_closed', 'true');
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());

    const queryString = query.toString();
    return useApi().get<ConversationListResponse>(`/admin/conversations${queryString ? `?${queryString}` : ''}`);
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
