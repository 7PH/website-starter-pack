// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { getErrorStatus, withStatus } from '~/utils/errors';

const PAGE_SIZE = 60;
// Same cap as the backend, below the host nginx body limit.
const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;
export const CMS_MEDIA_ACCEPT = 'image/jpeg,image/png,image/webp';

/** Status code of a failed upload → translation key. Mirrors the backend's 413/415/422/400. */
export function cmsUploadErrorKey(status: number | undefined): string {
    if (status === 401) return 'cms.media.errors.sessionExpired';
    if (status === 413) return 'cms.media.errors.tooBig';
    if (status === 415) return 'cms.media.errors.wrongType';
    if (status === 422) return 'cms.media.errors.tooManyPixels';
    if (status === 400) return 'cms.media.errors.unreadable';
    return 'cms.media.errors.generic';
}

/** One page-at-a-time view of the photo library, newest first. Each caller gets its own state. */
export function useCmsMediaLibrary() {
    const api = useApi();
    const items = ref<CmsMediaRead[]>([]);
    const total = ref(0);
    const loading = ref(false);
    const hasMore = computed(() => items.value.length < total.value);

    async function load(reset = false) {
        loading.value = true;
        try {
            const offset = reset ? 0 : items.value.length;
            const page = await api.get<CmsMediaListResponse>('/cms/media', { offset, limit: PAGE_SIZE });
            items.value = reset ? page.items : [...items.value, ...page.items];
            total.value = page.total;
        } finally {
            loading.value = false;
        }
    }

    function add(media: CmsMediaRead) {
        if (items.value.some((m) => m.id === media.id)) return;
        items.value.unshift(media);
        total.value++;
    }

    function replace(media: CmsMediaRead) {
        items.value = items.value.map((m) => (m.id === media.id ? media : m));
    }

    function remove(id: number) {
        items.value = items.value.filter((m) => m.id !== id);
        total.value--;
    }

    return { items, total, loading, hasMore, load, add, replace, remove };
}

/**
 * Delete a photo. Returns the pages still showing it (409, nothing deleted), or [] once deleted.
 * Raw fetch: useApi reduces error bodies to a message and the 409 body carries the page list.
 */
export async function deleteCmsMedia(id: number): Promise<CmsMediaUsage[]> {
    const auth = useAuth();
    const response = await fetch(`${useRuntimeConfig().public.apiBase}/cms/media/${id}`, {
        method: 'DELETE',
        headers: auth.token ? { Authorization: `Bearer ${auth.token.access_token}` } : {},
    });
    if (response.ok) return [];
    const body = await response.json().catch(() => ({}));
    if (response.status === 409 && body.pages?.length) return body.pages;
    // Anything else failed: never report it as deleted.
    throw withStatus(new Error(body.detail ?? response.statusText), response.status);
}

/**
 * POST one file with upload progress. useApi can't do this: it forces a JSON
 * content type and fetch() has no upload progress events.
 */
function uploadWithProgress(
    url: string,
    token: string | undefined,
    file: File,
    onProgress: (ratio: number) => void,
): Promise<CmsMediaRead> {
    const form = new FormData();
    form.append('file', file);
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(e.loaded / e.total);
        xhr.responseType = 'json';
        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300 && xhr.response) resolve(xhr.response);
            else reject(withStatus(new Error(xhr.statusText), xhr.status));
        };
        // A promise left pending would stall every upload queued after this one.
        xhr.onerror = xhr.onabort = xhr.ontimeout = () => reject(new Error('Network error'));
        xhr.send(form);
    });
}

export interface CmsUploadItem {
    key: number;
    name: string;
    progress: number;
    errorKey?: string;
}

// Module-level so uploads keep going (and stay visible) when the picker is closed and reopened.
// Only written in the browser, so nothing leaks between SSR requests.
const queue = ref<CmsUploadItem[]>([]);
const listeners = new Set<(media: CmsMediaRead) => void>();
let nextKey = 0;
// Batches run in order, each after the previous one finished.
let chain = Promise.resolve();

/** Upload queue: files go one at a time so a phone on a weak connection isn't saturated. */
export function useCmsMediaUpload(onUploaded: (media: CmsMediaRead) => void) {
    // Resolved here: Nuxt composables aren't available after an await in the upload loop.
    const url = `${useRuntimeConfig().public.apiBase}/cms/media`;
    const auth = useAuth();

    onMounted(() => listeners.add(onUploaded));
    onUnmounted(() => listeners.delete(onUploaded));

    function enqueue(files: File[]) {
        const pending: [CmsUploadItem, File][] = files.map((file) => {
            const item: CmsUploadItem = { key: nextKey++, name: file.name, progress: 0 };
            if (file.size > MAX_UPLOAD_BYTES) item.errorKey = cmsUploadErrorKey(413);
            // Empty type: the browser doesn't know, let the server decide.
            else if (file.type && !CMS_MEDIA_ACCEPT.split(',').includes(file.type))
                item.errorKey = cmsUploadErrorKey(415);
            return [item, file];
        });
        queue.value.push(...pending.map(([item]) => item));
        const valid = pending.filter(([item]) => !item.errorKey);
        chain = chain.then(() => run(valid));
    }

    async function run(pending: [CmsUploadItem, File][]) {
        for (const [item, file] of pending) {
            // Look the item up through the ref so progress updates are reactive.
            const live = () => queue.value.find((i) => i.key === item.key);
            try {
                const media = await uploadWithProgress(url, auth.token?.access_token, file, (ratio) => {
                    const target = live();
                    if (target) target.progress = ratio;
                });
                queue.value = queue.value.filter((i) => i.key !== item.key);
                listeners.forEach((listener) => listener(media));
            } catch (error) {
                const status = getErrorStatus(error);
                // Same as useApi on an expired token: drop it so the user logs in again.
                if (status === 401) auth.logout();
                const target = live();
                if (target) target.errorKey = cmsUploadErrorKey(status);
            }
        }
    }

    function dismiss(key: number) {
        queue.value = queue.value.filter((i) => i.key !== key);
    }

    return { queue, enqueue, dismiss };
}
