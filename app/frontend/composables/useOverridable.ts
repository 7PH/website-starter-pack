// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { Component } from 'vue';
import { componentOverrides } from '~/config/component-overrides';

/**
 * Returns the override registered for `name`, or `defaultComponent` if none.
 *
 * Sub-apps register overrides in `config/component-overrides.ts`. Values
 * are plain Vue components — for lazy-loaded overrides, wrap with
 * `defineAsyncComponent` from Vue.
 *
 * @example
 * ```ts
 * import DefaultModal from '~/components/organizations/CreateModal.vue';
 * const Modal = useOverridable('OrganizationsCreateModal', DefaultModal);
 * ```
 *
 * In template:
 * ```vue
 * <component :is="Modal" v-model:open="open" @create="handleCreate" />
 * ```
 */
export function useOverridable<T extends Component>(name: string, defaultComponent: T): T | Component {
    return componentOverrides[name] ?? defaultComponent;
}
