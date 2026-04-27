<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
/**
 * Paste-a-list bulk-import modal.
 *
 * The owner pastes one name per line; the modal auto-detects the delimiter
 * (comma, semicolon, tab, space) and shows a live preview. A "Last name first"
 * toggle swaps order before composing the display name as `"First LASTNAME"`.
 *
 * Submission posts to `/me/managed-account-groups/:id/managed-accounts/bulk`,
 * which silently dedupes against existing names in the group.
 */

const props = defineProps<{
    open: boolean;
    groupId: number;
}>();

const emit = defineEmits<{
    'update:open': [value: boolean];
    imported: [count: number];
}>();

const { t } = useI18n();
const { showError, showSuccess } = useToastHelpers();
const composable = useManagedAccountGroup();

type Delimiter = ',' | ';' | '\t' | ' ';

// ~1000 typical name lines, well under any browser textarea perf cliff.
const MAX_CSV_CHARS = 32_000;

const isOpen = computed({
    get: () => props.open,
    set: (v: boolean) => emit('update:open', v),
});

const csvText = ref('');
const lastNameFirst = ref(false);
const submitting = ref(false);
const userOverrodeDelimiter = ref(false);
const selectedDelimiter = ref<Delimiter>(',');

const delimiterOptions = computed<{ label: string; value: Delimiter }[]>(() => [
    { label: t('core.managed_accounts.import.delimiterComma'), value: ',' },
    { label: t('core.managed_accounts.import.delimiterSemicolon'), value: ';' },
    { label: t('core.managed_accounts.import.delimiterTab'), value: '\t' },
    { label: t('core.managed_accounts.import.delimiterSpace'), value: ' ' },
]);

function detectDelimiter(text: string): Delimiter {
    const lines = text.split('\n').filter((l) => l.trim());
    const counts: Record<string, number> = { ',': 0, ';': 0, '\t': 0 };
    for (const line of lines) {
        for (const d of [',', ';', '\t'] as const) {
            if (line.includes(d)) counts[d] = (counts[d] ?? 0) + 1;
        }
    }
    const best = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    if (best && best[1] > 0) return best[0] as Delimiter;
    return ' ';
}

watch(csvText, (text) => {
    if (!userOverrodeDelimiter.value && text.trim()) {
        selectedDelimiter.value = detectDelimiter(text);
    }
});

// Reset state every time the modal re-opens.
watch(isOpen, (open) => {
    if (open) {
        csvText.value = '';
        lastNameFirst.value = false;
        userOverrodeDelimiter.value = false;
        selectedDelimiter.value = ',';
    }
});

function onDelimiterChange(value: Delimiter) {
    selectedDelimiter.value = value;
    userOverrodeDelimiter.value = true;
}

interface PreviewRow {
    first_name: string;
    last_name: string;
    display_name: string;
}

const preview = computed<PreviewRow[]>(() => {
    if (!csvText.value.trim()) return [];
    const delim = selectedDelimiter.value;
    return csvText.value
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
            const parts = delim === ' ' ? line.split(/\s+/, 2) : line.split(delim, 2);
            let first = (parts[0] ?? '').trim();
            let last = (parts[1] ?? '').trim();
            if (lastNameFirst.value) [first, last] = [last, first];
            // Normalize: title-case first, uppercase last (matches the domatex convention).
            const niceFirst = first.charAt(0).toUpperCase() + first.slice(1);
            const niceLast = last.toUpperCase();
            const display_name = [niceFirst, niceLast].filter(Boolean).join(' ');
            return { first_name: niceFirst, last_name: niceLast, display_name };
        })
        .filter((s) => s.display_name);
});

const canSubmit = computed(() => !submitting.value && preview.value.length > 0);

async function submit() {
    if (!canSubmit.value) return;
    submitting.value = true;
    try {
        const result = await composable.bulkCreateAccounts(props.groupId, {
            accounts: preview.value.map((p) => ({ display_name: p.display_name })),
        });
        showSuccess(
            t('core.managed_accounts.import.importSuccess', {
                n: result.accounts.length,
                skipped: result.skipped,
            }),
        );
        emit('imported', result.accounts.length);
        isOpen.value = false;
    } catch (error) {
        showError(error, 'core.managed_accounts.import.importFailed');
    } finally {
        submitting.value = false;
    }
}
</script>

<template>
    <UModal v-model:open="isOpen">
        <template #content>
            <UCard>
                <template #header>
                    <UiModalHeader :title="t('core.managed_accounts.import.importTitle')" @close="isOpen = false" />
                </template>

                <div class="import-form">
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        {{ t('core.managed_accounts.import.importHelp') }}
                    </p>

                    <UTextarea
                        v-model="csvText"
                        :placeholder="t('core.managed_accounts.import.importPlaceholder')"
                        :rows="8"
                        :maxlength="MAX_CSV_CHARS"
                        class="w-full font-mono text-sm"
                    />

                    <div class="import-options">
                        <UFormField :label="t('core.managed_accounts.import.delimiter')">
                            <USelect
                                :model-value="selectedDelimiter"
                                :items="delimiterOptions"
                                value-key="value"
                                size="sm"
                                @update:model-value="onDelimiterChange"
                            />
                        </UFormField>
                        <UCheckbox v-model="lastNameFirst" :label="t('core.managed_accounts.import.lastNameFirst')" />
                    </div>

                    <div v-if="preview.length > 0" class="preview-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>{{ t('core.managed_accounts.import.colFirstName') }}</th>
                                    <th>{{ t('core.managed_accounts.import.colLastName') }}</th>
                                    <th>{{ t('core.managed_accounts.import.colDisplayName') }}</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(row, i) in preview" :key="i">
                                    <td>{{ row.first_name }}</td>
                                    <td class="font-semibold">{{ row.last_name }}</td>
                                    <td class="text-gray-500 dark:text-gray-400">{{ row.display_name }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <p v-else-if="csvText.trim()" class="text-sm text-gray-500 dark:text-gray-400">
                        {{ t('core.managed_accounts.import.importEmpty') }}
                    </p>
                </div>

                <template #footer>
                    <UiFormActions>
                        <UButton
                            color="neutral"
                            variant="outline"
                            :label="t('core.common.cancel')"
                            @click="isOpen = false"
                        />
                        <UButton
                            :label="t('core.managed_accounts.import.importSubmit', { n: preview.length })"
                            :loading="submitting"
                            :disabled="!canSubmit"
                            @click="submit"
                        />
                    </UiFormActions>
                </template>
            </UCard>
        </template>
    </UModal>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.import-form {
    @apply flex flex-col gap-4;
}

.import-options {
    @apply flex flex-wrap items-end gap-4;
}

.preview-table {
    @apply max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg text-sm;
}

.preview-table table {
    @apply w-full;
}

.preview-table thead {
    @apply sticky top-0 bg-gray-50 dark:bg-gray-800;
}

.preview-table th {
    @apply text-left px-3 py-1.5 text-gray-500 dark:text-gray-400 font-medium;
}

.preview-table tbody {
    @apply divide-y divide-gray-100 dark:divide-gray-800;
}

.preview-table td {
    @apply px-3 py-1.5 text-gray-700 dark:text-gray-300;
}
</style>
