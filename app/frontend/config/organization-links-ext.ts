/**
 * Where core links to an organization go: the card in the account's organizations tab, the "Manage organization"
 * buttons of the billing tab, and the page opened after creating one.
 *
 * Return null (the default) for the core page, /organizations/{id}. An app with its own organization page returns its
 * URL instead. `tab` is the section the link is about ('billing' from the billing tab), undefined otherwise.
 *
 * @example
 * export function organizationLinkExt(organizationId: number, tab?: string): string | null {
 *     return tab === 'billing' ? null : `/school/${organizationId}`;
 * }
 */
export function organizationLinkExt(_organizationId: number, _tab?: string): string | null {
    return null;
}
