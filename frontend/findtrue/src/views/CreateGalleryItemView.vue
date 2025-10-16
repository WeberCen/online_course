<template>
  <div class="create-view-container">
    <h2>{{ isEditMode ? '编辑作品' : '上传新作品' }}</h2>
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="title">作品名称</label>
        <input type="text" id="title" v-model="itemData.title" required>
      </div>

      <div class="form-group">
        <label for="description">作品描述</label>
        <p class="field-help">您可以使用富文本编辑器来详细介绍您的作品。</p>
        <RichTextEditor v-model="itemData.description" />
      </div>

      <div class="form-group">
        <label for="coverImage">作品封面图片</label>
        <input type="file" id="coverImage" @change="handleCoverImageChange" accept="image/*">
        </div>

      <div class="form-group">
        <label for="workFile">作品文件 (例如 .zip, .rar)</label>
        <input type="file" id="workFile" @change="handleWorkFileChange" :required="!isEditMode">
        <p v-if="isEditMode" class="field-help">注意：如需更新作品文件，请上传新文件。否则将保留原文件。</p>
      </div>

      <div class="form-group">
        <label for="version">版本号</label>
        <input type="text" id="version" v-model="itemData.version" required placeholder="例如: 1.0">
      </div>

       <div class="form-group">
        <label for="requiredPoints">所需积分</label>
        <input type="number" id="requiredPoints" v-model.number="itemData.requiredPoints" min="0">
      </div>

      <div class="form-group checkbox-group">
        <input type="checkbox" id="is_vip_free" v-model="itemData.is_vip_free">
        <label for="is_vip_free">此作品对 VIP 免费</label>
      </div>
      
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSubmitting">{{ isSubmitting ? '保存中...' : (isEditMode ? '保存修改' : '提交审核') }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { createGalleryItem, updateGalleryItem, getGalleryWorkDetail } from '@/services/apiService';
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue';

const router = useRouter();
const route = useRoute();

const itemId = computed(() => route.params.id as string | undefined);
const isEditMode = computed(() => !!itemId.value);

const itemData = reactive({
  title: '',
  description: '',
  coverImage: null as File | null,
  workFile: null as File | null,
  version: '1.0',
  requiredPoints: 0,
  is_vip_free: false,
});
const isSubmitting = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  if (isEditMode.value && itemId.value) {
    try {
      const data = await getGalleryWorkDetail(itemId.value);
      itemData.title = data.title;
      itemData.description = data.description;
      itemData.version = data.version;
      itemData.requiredPoints = data.requiredPoints;
      itemData.is_vip_free = data.is_vip_free;
    } catch (err) {
      console.error("加载作品详情失败:", err);
      if (isAxiosError(err) && err.response?.status === 404) {
        error.value = "找不到指定的作品。";
      } else {
        error.value = '加载作品详情失败，请稍后再试。';
      }
    }
  }
});

const handleCoverImageChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    itemData.coverImage = target.files[0]!;
  } else {
    itemData.coverImage = null;
  }
};

const handleWorkFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    itemData.workFile = target.files[0]!;
  } else {
    itemData.workFile = null;
  }
};

const submitForm = async () => {
  if (!isEditMode.value && !itemData.workFile) {
    alert("创建新作品时，必须上传作品文件。");
    return;
  }
  isSubmitting.value = true;
  error.value = null;

  const formData = new FormData();
  formData.append('title', itemData.title);
  formData.append('description', itemData.description);
  formData.append('version', itemData.version);
  formData.append('requiredPoints', String(itemData.requiredPoints));
  formData.append('is_vip_free', String(itemData.is_vip_free));
  
  if (itemData.workFile) {
    formData.append('workFile', itemData.workFile);
  }
  if (itemData.coverImage) {
    formData.append('coverImage', itemData.coverImage);
  }

  try {
    if (isEditMode.value && itemId.value) {
      const updatedItem = await updateGalleryItem(itemId.value, formData);
      alert('作品更新成功，已重新提交审核！');
      router.push({ name: 'gallery-detail', params: { id: String(updatedItem.id) } });
    } else {
      const newItem = await createGalleryItem(formData);
      alert('作品上传成功，已提交审核！');
      router.push({ name: 'gallery-detail', params: { id: String(newItem.id) } });
    }
  } catch (err) {
    console.error("操作失败:", err);
    if (isAxiosError(err)) {
      if (err.response?.status === 403) {
        error.value = "抱歉，您没有权限执行此操作。";
      } else {
        const errorData = err.response?.data;
        if (typeof errorData === 'object' && errorData !== null) {
          error.value = `操作失败: ${Object.values(errorData).flat().join(' ')}`;
        } else {
          error.value = "操作失败，请检查您的输入或网络连接。";
        }
      }
    } else {
      error.value = '发生未知错误，请重试。';
    }
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.create-view-container { max-width: 800px; margin: 2rem auto; }
.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
.checkbox-group { display: flex; align-items: center; }
.checkbox-group input { width: auto; margin-right: 0.5rem; }
.field-help { font-size: 0.8rem; color: #666; margin-top: 0.2rem; }
button { padding: 10px 20px; border: none; background-color: #007bff; color: white; border-radius: 4px; cursor: pointer; font-size: 1rem; }
button:disabled { background-color: #a0cffc; }
.error { color: red; margin-bottom: 1rem; }
</style>