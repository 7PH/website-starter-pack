<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Imports TipTap: only use it lazily (<LazyCmsRichTextEditor>) so it stays out of public bundles.
import Image from '@tiptap/extension-image';
import StarterKit from '@tiptap/starter-kit';
import { EditorContent, useEditor } from '@tiptap/vue-3';
import { inlineImageSrc, normalizeLink, RICH_TEXT_CLASS } from '~/utils/cms';

const html = defineModel<string>({ default: '' });

const { t } = useI18n();
const { showWarning } = useToastHelpers();

// data-media-id ties the photo to the library so it can't be deleted while used. Pasted foreign images are refused
// here: the server would drop them on save while the editor kept showing them.
const LibraryImage = Image.extend({
    parseHTML() {
        return [{ tag: 'img[src][data-media-id]' }];
    },
    addAttributes() {
        return {
            ...this.parent?.(),
            mediaId: {
                default: null,
                parseHTML: (el) => el.getAttribute('data-media-id'),
                renderHTML: (attrs) => (attrs.mediaId ? { 'data-media-id': attrs.mediaId } : {}),
            },
        };
    },
});

const editor = useEditor({
    content: html.value,
    // Only what the server keeps (helpers/sanitize.py), so nothing typed here disappears on save.
    extensions: [
        StarterKit.configure({
            heading: { levels: [2, 3] },
            code: false,
            codeBlock: false,
            horizontalRule: false,
            strike: false,
            underline: false,
            // No autolink: it makes the link mark inclusive, so text typed right after a link would join it.
            link: { openOnClick: false, autolink: false, HTMLAttributes: { target: null, rel: null } },
        }),
        LibraryImage,
    ],
    editorProps: { attributes: { class: `${RICH_TEXT_CLASS} min-h-48 px-4 py-2 focus:outline-none` } },
    onUpdate: ({ editor }) => (html.value = editor.getHTML()),
});

// Content replaced from outside (eg the sanitized HTML a save returns). Our own updates equal getHTML(), so typing is untouched.
watch(html, (value) => {
    const e = editor.value;
    if (!e || value === e.getHTML()) return;
    const { from } = e.state.selection;
    e.commands.setContent(value, { emitUpdate: false });
    e.commands.setTextSelection(Math.min(from, e.state.doc.content.size));
});

const tools = computed(() => {
    const e = editor.value;
    if (!e) return [];
    const chain = () => e.chain().focus();
    return [
        {
            icon: 'i-lucide-heading-2',
            label: t('cms.pages.editor.heading'),
            active: e.isActive('heading', { level: 2 }),
            run: () => chain().toggleHeading({ level: 2 }).run(),
        },
        {
            icon: 'i-lucide-heading-3',
            label: t('cms.pages.editor.subheading'),
            active: e.isActive('heading', { level: 3 }),
            run: () => chain().toggleHeading({ level: 3 }).run(),
        },
        {
            icon: 'i-lucide-bold',
            label: t('cms.pages.editor.bold'),
            active: e.isActive('bold'),
            run: () => chain().toggleBold().run(),
        },
        {
            icon: 'i-lucide-italic',
            label: t('cms.pages.editor.italic'),
            active: e.isActive('italic'),
            run: () => chain().toggleItalic().run(),
        },
        {
            icon: 'i-lucide-list',
            label: t('cms.pages.editor.bulletList'),
            active: e.isActive('bulletList'),
            run: () => chain().toggleBulletList().run(),
        },
        {
            icon: 'i-lucide-list-ordered',
            label: t('cms.pages.editor.orderedList'),
            active: e.isActive('orderedList'),
            run: () => chain().toggleOrderedList().run(),
        },
        {
            icon: 'i-lucide-quote',
            label: t('cms.pages.editor.quote'),
            active: e.isActive('blockquote'),
            run: () => chain().toggleBlockquote().run(),
        },
    ];
});

const linkOpen = ref(false);
const linkUrl = ref('');

watch(linkOpen, (open) => {
    if (open) linkUrl.value = editor.value?.getAttributes('link').href ?? '';
});

function applyLink(value = linkUrl.value) {
    const e = editor.value;
    if (!e) return;
    const href = normalizeLink(value);
    // Nothing selected, not in a link: insert the address itself as the link text.
    if (href && e.state.selection.empty && !e.isActive('link')) {
        e.chain()
            .focus()
            .insertContent({ type: 'text', text: value.trim(), marks: [{ type: 'link', attrs: { href } }] })
            .run();
    } else {
        const chain = e.chain().focus().extendMarkRange('link');
        if (!href) chain.unsetLink().run();
        else if (!chain.setLink({ href }).run()) return showWarning(t('cms.pages.editor.linkInvalid'));
    }
    linkOpen.value = false;
}

const pickerOpen = ref(false);

// "HTML" view of the same content, like WordPress's "Text" tab. The server cleans it on save like anything typed visually.
const sourceMode = ref(false);
const source = ref('');
function toggleSource() {
    // One block per line, readable without changing the content: switching views alone never marks the page as modified.
    if (!sourceMode.value)
        source.value = html.value.replace(/(<\/(?:p|h2|h3|ul|ol|li|blockquote)>)(?!\n)/g, '$1\n').trim();
    sourceMode.value = !sourceMode.value;
}
function onSourceInput(value: string) {
    source.value = value;
    html.value = value;
}

function insertImage(media: CmsMediaRead) {
    editor.value
        ?.chain()
        .focus()
        .insertContent({ type: 'image', attrs: { src: inlineImageSrc(media), alt: media.alt, mediaId: media.id } })
        // Inserted at the end of a paragraph, the image ends up selected and typing would replace it: move into the text after it.
        .command(({ tr, commands }) => {
            const { empty, $to } = tr.selection;
            if (empty && $to.parent.isTextblock) return true;
            return $to.nodeAfter?.isTextblock ? commands.setTextSelection($to.pos + 1) : commands.createParagraphNear();
        })
        .run();
    pickerOpen.value = false;
}

// Closing the picker would give focus back to the toolbar button: keep it in the text, after the photo.
function keepEditorFocus(event: Event) {
    event.preventDefault();
    editor.value?.commands.focus();
}
</script>

<template>
    <div class="rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div v-if="editor" class="flex flex-wrap gap-1 p-1 border-b border-gray-200 dark:border-gray-800">
            <template v-if="!sourceMode">
                <UTooltip v-for="tool in tools" :key="tool.icon" :text="tool.label">
                    <UButton
                        :icon="tool.icon"
                        :aria-label="tool.label"
                        :color="tool.active ? 'primary' : 'neutral'"
                        :variant="tool.active ? 'soft' : 'ghost'"
                        size="sm"
                        @click="tool.run"
                    />
                </UTooltip>
                <UPopover v-model:open="linkOpen">
                    <UTooltip :text="t('cms.pages.editor.link')">
                        <UButton
                            icon="i-lucide-link"
                            :aria-label="t('cms.pages.editor.link')"
                            :color="editor.isActive('link') ? 'primary' : 'neutral'"
                            :variant="editor.isActive('link') ? 'soft' : 'ghost'"
                            size="sm"
                        />
                    </UTooltip>
                    <template #content>
                        <form class="flex flex-col gap-2 p-3 w-80" @submit.prevent="applyLink()">
                            <UFormField :label="t('cms.pages.editor.linkUrl')">
                                <UInput v-model="linkUrl" placeholder="https://" class="w-full" autofocus />
                            </UFormField>
                            <div class="flex justify-end gap-2">
                                <UButton
                                    v-if="editor.isActive('link')"
                                    :label="t('cms.pages.editor.unlink')"
                                    color="neutral"
                                    variant="ghost"
                                    @click="applyLink('')"
                                />
                                <UButton type="submit" :label="t('cms.pages.editor.apply')" />
                            </div>
                        </form>
                    </template>
                </UPopover>
                <UTooltip :text="t('cms.pages.editor.image')">
                    <UButton
                        icon="i-lucide-image"
                        :aria-label="t('cms.pages.editor.image')"
                        color="neutral"
                        variant="ghost"
                        size="sm"
                        @click="pickerOpen = true"
                    />
                </UTooltip>
            </template>
            <UButton
                :icon="sourceMode ? 'i-lucide-type' : 'i-lucide-code-xml'"
                :label="sourceMode ? t('cms.pages.editor.visual') : 'HTML'"
                color="neutral"
                :variant="sourceMode ? 'soft' : 'ghost'"
                size="sm"
                class="ml-auto"
                @click="toggleSource"
            />
        </div>
        <div v-if="sourceMode" class="flex flex-col gap-1 p-2">
            <UTextarea
                :model-value="source"
                :rows="12"
                autoresize
                :maxrows="30"
                class="w-full"
                :ui="{ base: 'font-mono text-sm' }"
                @update:model-value="onSourceInput"
            />
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ t('cms.pages.editor.sourceHelp') }}</p>
        </div>
        <!-- The text scrolls inside the box, so the toolbar above it never leaves the screen on long content. -->
        <EditorContent v-show="!sourceMode" :editor="editor" class="max-h-[65vh] overflow-y-auto" />
        <CmsMediaPicker
            v-model:open="pickerOpen"
            :content="{ onCloseAutoFocus: keepEditorFocus }"
            @select="insertImage"
        />
    </div>
</template>
