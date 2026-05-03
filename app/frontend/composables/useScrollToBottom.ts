// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Auto-scrolls a container to the bottom on mount and whenever ``trigger``
 * changes. Returns the container ref to bind on the scrollable element and
 * a manual ``scrollToBottom`` to call after appending content.
 */
export function useScrollToBottom(trigger: () => unknown) {
    const container = ref<HTMLElement | null>(null);

    function scrollToBottom() {
        if (container.value) container.value.scrollTop = container.value.scrollHeight;
    }

    onMounted(() => nextTick(scrollToBottom));
    watch(trigger, () => nextTick(scrollToBottom));

    return { container, scrollToBottom };
}
