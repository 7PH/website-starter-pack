// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Conversation subtype configuration.
 * Projects can extend by creating config/conversation-subtypes-ext.ts with PROJECT_CONVERSATION_SUBTYPES.
 */

/** Any user-initiable subtype value the backend currently accepts. Generated
 *  from the Pydantic union so it stays in sync with core + project enums. */
export type ConversationSubtypeValue = NonNullable<ConversationCreate['subtype']>;

export interface ConversationSubtype {
    /** Internal value sent to the API (e.g. "organization_request") */
    value: ConversationSubtypeValue;
    /** Display label in admin UI (e.g. "Organization Request") */
    label: string;
}

export const CORE_CONVERSATION_SUBTYPES: ConversationSubtype[] = [
    { value: 'bug_report', label: 'Bug report' },
    { value: 'feature_request', label: 'Feature request' },
];
