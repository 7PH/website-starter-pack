// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

export interface TableStateOptions {
    /** Default items per page */
    defaultLimit?: number;
    /** Debounce delay for search in ms */
    searchDebounce?: number;
    /** Default sort field */
    defaultSort?: string;
    /** Default sort order */
    defaultOrder?: 'asc' | 'desc';
}

export interface TableState {
    search: Ref<string>;
    page: Ref<number>;
    limit: Ref<number>;
    offset: ComputedRef<number>;
    sort: Ref<string>;
    order: Ref<'asc' | 'desc'>;
    debouncedSearch: Ref<string>;
}

/**
 * Composable for managing table state including search, pagination, and sorting.
 * Provides debounced search and computed offset for API calls.
 */
export function useTableState(options: TableStateOptions = {}): TableState & {
    reset: () => void;
    setPage: (newPage: number) => void;
    nextPage: () => void;
    prevPage: () => void;
    toggleSort: (field: string) => void;
} {
    const { defaultLimit = 50, searchDebounce = 300, defaultSort = '', defaultOrder = 'desc' } = options;

    // Core state
    const search = ref('');
    const page = ref(1);
    const limit = ref(defaultLimit);
    const sort = ref(defaultSort);
    const order = ref<'asc' | 'desc'>(defaultOrder);

    // Debounced search for API calls
    const debouncedSearch = refDebounced(search, searchDebounce);

    // Computed offset for pagination
    const offset = computed(() => (page.value - 1) * limit.value);

    // Reset search resets page to 1
    watch(debouncedSearch, () => {
        page.value = 1;
    });

    // Reset all state
    function reset() {
        search.value = '';
        page.value = 1;
        limit.value = defaultLimit;
        sort.value = defaultSort;
        order.value = defaultOrder;
    }

    // Page navigation
    function setPage(newPage: number) {
        if (newPage >= 1) {
            page.value = newPage;
        }
    }

    function nextPage() {
        page.value++;
    }

    function prevPage() {
        if (page.value > 1) {
            page.value--;
        }
    }

    // Toggle sort - clicking same field toggles order, new field resets to desc
    function toggleSort(field: string) {
        if (sort.value === field) {
            order.value = order.value === 'asc' ? 'desc' : 'asc';
        } else {
            sort.value = field;
            order.value = 'desc';
        }
        page.value = 1;
    }

    return {
        // State
        search,
        page,
        limit,
        offset,
        sort,
        order,
        debouncedSearch,

        // Actions
        reset,
        setPage,
        nextPage,
        prevPage,
        toggleSort,
    };
}
