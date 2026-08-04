<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useEditor, EditorContent } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import DOMPurify from 'dompurify';

// Content can come from the backend (previously saved) or from other admin
// sessions — sanitize before it ever touches the (contenteditable) DOM.
const sanitize = (html: string): string =>
  DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'h2', 'h3', 'ul', 'ol', 'li', 'a'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
  });

const props = withDefaults(
  defineProps<{
    modelValue: string;
    // 'full' = headings + lists (default). 'inline' = only bold/italic/link,
    // for single-line fields like a course subtitle where block nodes would
    // break card layouts.
    variant?: 'full' | 'inline';
    placeholder?: string;
  }>(),
  { variant: 'full', placeholder: '' },
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const isEmpty = ref(true);
const showBlockTools = computed(() => props.variant !== 'inline');

const editor = useEditor({
  content: sanitize(props.modelValue || ''),
  extensions: [
    StarterKit,
    Link.configure({
      openOnClick: false,
      autolink: true,
      HTMLAttributes: { rel: 'noopener noreferrer', target: '_blank' },
    }),
  ],
  editorProps: {
    attributes: {
      class: 'prose-editor focus:outline-none px-3 py-2 text-sm',
    },
  },
  onUpdate: ({ editor: ed }) => {
    isEmpty.value = ed.isEmpty;
    emit('update:modelValue', ed.getHTML());
  },
});

// Hydrate external changes (e.g. loading a topic) without stomping the cursor
// while the user is actively typing.
watch(
  () => props.modelValue,
  (value) => {
    const ed = editor.value;
    if (!ed) return;
    const incoming = sanitize(value || '');
    if (incoming === ed.getHTML()) return;
    ed.commands.setContent(incoming, { emitUpdate: false });
    isEmpty.value = ed.isEmpty;
  },
);

const setLink = () => {
  const ed = editor.value;
  if (!ed) return;
  const previousUrl = ed.getAttributes('link').href as string | undefined;
  const url = window.prompt('URL del enlace', previousUrl || 'https://');
  if (url === null) return;
  if (url === '') {
    ed.chain().focus().extendMarkRange('link').unsetLink().run();
    return;
  }
  ed.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
};

onMounted(() => {
  editor.value?.commands.setContent(sanitize(props.modelValue || ''), { emitUpdate: false });
  isEmpty.value = editor.value?.isEmpty ?? true;
});

onBeforeUnmount(() => {
  editor.value?.destroy();
});

const isActive = (name: string, attrs?: Record<string, any>) => editor.value?.isActive(name, attrs) ?? false;
</script>

<template>
  <div class="rich-text-editor border border-[var(--color-border)] rounded-xl overflow-hidden bg-[var(--color-surface)]">
    <div v-if="editor" class="flex flex-wrap items-center gap-1 border-b border-[var(--color-border)] bg-[var(--color-app-bg)] px-2 py-1.5">
      <button type="button" class="toolbar-btn" :class="{ 'is-active': isActive('bold') }" @click="editor.chain().focus().toggleBold().run()" title="Negrita">
        <strong>B</strong>
      </button>
      <button type="button" class="toolbar-btn italic" :class="{ 'is-active': isActive('italic') }" @click="editor.chain().focus().toggleItalic().run()" title="Cursiva">
        I
      </button>
      <template v-if="showBlockTools">
        <span class="w-px h-5 bg-[var(--color-border)] mx-1"></span>
        <button type="button" class="toolbar-btn" :class="{ 'is-active': isActive('heading', { level: 2 }) }" @click="editor.chain().focus().toggleHeading({ level: 2 }).run()" title="Título H2">
          H2
        </button>
        <button type="button" class="toolbar-btn" :class="{ 'is-active': isActive('heading', { level: 3 }) }" @click="editor.chain().focus().toggleHeading({ level: 3 }).run()" title="Título H3">
          H3
        </button>
        <span class="w-px h-5 bg-[var(--color-border)] mx-1"></span>
        <button type="button" class="toolbar-btn" :class="{ 'is-active': isActive('bulletList') }" @click="editor.chain().focus().toggleBulletList().run()" title="Lista con viñetas">
          •
        </button>
        <button type="button" class="toolbar-btn" :class="{ 'is-active': isActive('orderedList') }" @click="editor.chain().focus().toggleOrderedList().run()" title="Lista numerada">
          1.
        </button>
      </template>
      <span class="w-px h-5 bg-[var(--color-border)] mx-1"></span>
      <button type="button" class="toolbar-btn" :class="{ 'is-active': isActive('link') }" @click="setLink" title="Enlace">
        🔗
      </button>
      <button type="button" class="toolbar-btn" @click="editor.chain().focus().unsetAllMarks().clearNodes().run()" title="Quitar formato">
        ✕
      </button>
    </div>
    <div class="relative">
      <p
        v-if="placeholder && isEmpty"
        class="pointer-events-none absolute left-3 top-2 text-sm text-[var(--color-text-muted)] select-none"
      >
        {{ placeholder }}
      </p>
      <EditorContent :editor="editor" :class="variant === 'inline' ? 'editor-inline' : 'editor-full'" />
    </div>
  </div>
</template>

<style scoped>
.toolbar-btn {
  min-width: 1.75rem;
  height: 1.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}
.toolbar-btn:hover {
  background: var(--color-primary-soft);
  color: var(--color-text);
}
.toolbar-btn.is-active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
.toolbar-btn.italic {
  font-style: italic;
}

.rich-text-editor :deep(.prose-editor) {
  color: var(--color-text);
}
.editor-full :deep(.prose-editor) {
  min-height: 10rem;
}
.editor-inline :deep(.prose-editor) {
  min-height: 2.5rem;
}
.rich-text-editor :deep(.prose-editor p) {
  margin: 0.5em 0;
}
.rich-text-editor :deep(.prose-editor h2) {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0.75em 0 0.375em;
}
.rich-text-editor :deep(.prose-editor h3) {
  font-size: 1.0625rem;
  font-weight: 600;
  margin: 0.75em 0 0.375em;
}
.rich-text-editor :deep(.prose-editor ul) {
  list-style: disc;
  padding-left: 1.5rem;
  margin: 0.5em 0;
}
.rich-text-editor :deep(.prose-editor ol) {
  list-style: decimal;
  padding-left: 1.5rem;
  margin: 0.5em 0;
}
.rich-text-editor :deep(.prose-editor a) {
  color: var(--color-primary);
  text-decoration: underline;
}
</style>
