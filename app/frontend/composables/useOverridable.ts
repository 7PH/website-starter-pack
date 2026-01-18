// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { computed, ref, type Component, type ComputedRef } from 'vue';
import { componentOverrides } from '~/config/component-overrides';

// Cache for resolved async components
const resolvedComponents = new Map<string, Component>();

// Reactive trigger to force re-computation when async components resolve
const asyncLoadTrigger = ref(0);

/**
 * Returns an overridable component.
 *
 * Sub-apps can register overrides in config/component-overrides.ts to replace
 * core components with custom implementations.
 *
 * @param componentName - The override key (must match key in componentOverrides)
 * @param defaultComponent - The default component to use if no override exists
 * @returns A computed ref that resolves to the override or default component
 *
 * @example
 * ```ts
 * import DefaultModal from '~/components/organizations/CreateModal.vue';
 * const Modal = useOverridable('OrganizationsCreateModal', DefaultModal);
 * ```
 *
 * In template, use directly (Vue unwraps computed refs):
 * ```vue
 * <Modal v-model:open="open" @create="handleCreate" />
 * ```
 */
export function useOverridable<T extends Component>(
    componentName: string,
    defaultComponent: T,
): ComputedRef<T | Component> {
    return computed(() => {
        // Access trigger to make computed reactive to async loads
        // eslint-disable-next-line @typescript-eslint/no-unused-expressions
        asyncLoadTrigger.value;

        const loader = componentOverrides[componentName];

        if (!loader) {
            return defaultComponent;
        }

        // Check if we've already resolved this async component
        if (resolvedComponents.has(componentName)) {
            return resolvedComponents.get(componentName) as T;
        }

        // Start async load and return default while loading
        loader().then((mod) => {
            resolvedComponents.set(componentName, mod.default);
            // Trigger re-computation for all components using overrides
            asyncLoadTrigger.value++;
        });

        return defaultComponent;
    });
}
