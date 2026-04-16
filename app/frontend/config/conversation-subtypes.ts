// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Conversation subtype configuration.
 * Projects can extend by creating config/conversation-subtypes-ext.ts with PROJECT_CONVERSATION_SUBTYPES.
 */

export interface ConversationSubtype {
    /** Internal value sent to the API (e.g. "organization_request") */
    value: string;
    /** Display label in admin UI (e.g. "Organization Request") */
    label: string;
}

export const CORE_CONVERSATION_SUBTYPES: ConversationSubtype[] = [];
