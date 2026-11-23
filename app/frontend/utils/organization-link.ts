// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { organizationLinkExt } from '~/config/organization-links-ext';

/** Link to an organization: the app's own page (config/organization-links-ext.ts), else the core one. */
export function organizationLink(organizationId: number, tab?: string): string {
    return organizationLinkExt(organizationId, tab) ?? `/organizations/${organizationId}${tab ? `?tab=${tab}` : ''}`;
}
