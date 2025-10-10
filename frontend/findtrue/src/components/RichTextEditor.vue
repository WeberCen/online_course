<template>
  <div class="editor-container">
    <div v-if="editor" class="toolbar">
      <button @click="editor.chain().focus().toggleBold().run()" :class="{ 'is-active': editor.isActive('bold') }">Bold</button>
      <button @click="editor.chain().focus().toggleItalic().run()" :class="{ 'is-active': editor.isActive('italic') }">Italic</button>
      <button @click="triggerImageUpload">上传图片</button>
      <input type="file" ref="imageUploader" @change="handleImageUpload" accept="image/*" style="display: none;" />
    </div>
    <editor-content :editor="editor" />
  </div>
</template>

<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import { ref, watch } from 'vue';
import { uploadEditorImage } from '@/services/apiService';

const props = defineProps<{ modelValue: string }>();
const emit = defineEmits(['update:modelValue']);

const editor = useEditor({
  content: props.modelValue,
  extensions: [StarterKit, Image],
  onUpdate: () => {
    emit('update:modelValue', editor.value?.getHTML() || '');
  },
});

watch(() => props.modelValue, (newValue) => {
  if (editor.value?.getHTML() === newValue) return;
  editor.value?.commands.setContent(newValue, false);
});

const imageUploader = ref<HTMLInputElement | null>(null);

const triggerImageUpload = () => {
  imageUploader.value?.click();
};

const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file || !editor.value) return;

  try {
    const response = await uploadEditorImage(file);
    const url = response.data.imageUrl;
    editor.value.chain().focus().setImage({ src: url }).run();
  } catch (error) {
    console.error("Image upload failed:", error);
    alert("图片上传失败！");
  }
};
</script>

<style>
/* 简单的 Tiptap 编辑器样式 */
.ProseMirror { border: 1px solid #ccc; padding: 1rem; min-height: 200px; border-radius: 4px; }
.ProseMirror:focus { outline: none; border-color: #007bff; }
.toolbar { border: 1px solid #ccc; border-bottom: none; padding: 0.5rem; background-color: #f9f9f9; }
.toolbar button { margin-right: 0.5rem; }
.toolbar button.is-active { background-color: #007bff; color: white; }
</style>