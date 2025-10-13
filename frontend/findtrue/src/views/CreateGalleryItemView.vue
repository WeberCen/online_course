<template>
  <div class="create-gallery-item-view">
    <h2>创建新作品</h2>
    <form @submit.prevent="submitForm">
      <button type="submit" :disabled="isSubmitting">{{ isSubmitting ? '提交中...' : '提交审核' }}</button>
      <div class="form-gallery-item">
        <label for="name">作品名称</label>
        <input type="text" id="name" v-model="itemData.title" required>
      </div>
      <div class="form-gallery-item">
        <label for="description">作品描述</label>
        <RichTextEditor id="description" v-model="itemData.description" rows="5"></RichTextEditor>
      </div>
       <div class="form-gallery-item">
        <label for="coverImage">作品封面图片</label>
        <input type="file" id="coverImage" @change="handleCoverImageChange">
      </div>
       <div class="form-gallery-item">
        <label for="workFile">作品文件</label>
        <input type="file" id="workFile" @change="handleWorkFileChange">
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
        <label for="is_vip_free">VIP 免费</label>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSubmitting">{{ isSubmitting ? '提交中...' : '提交审核' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { createGalleryItem } from '@/services/apiService';
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue';

const router = useRouter();
const itemData = reactive({
  title: '',
  description: '',
  coverImage: null as String | File | null,
  workFile: null as String | File | null,
  version: '1.0',
  requiredPoints: 0,
  is_vip_free: false,
  tags:[],
});
const isSubmitting = ref(false);
const error = ref<string | null>(null);

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
    if (!itemData.workFile) {
        alert("请务必上传作品文件。");
        return;
    }
    if (!itemData.tags.length) {
        alert("请添加至少一个标签。");
        return;
    }
    if (!itemData.description) {
        alert("请添加作品描述。");
        return;
    }
    if (!itemData.title) {
        alert("请添加作品名称。");
        return;
    }
    if (!itemData.requiredPoints) {
        alert("请添加所需积分。");
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
  formData.append('tags', itemData.tags.join(','));
  if (itemData.workFile instanceof File) {
        // 情况 1: 用户上传了新的文件
        formData.append('workFile', itemData.workFile);
    } else if (typeof itemData.workFile === 'string' && itemData.workFile) {
        // 情况 2: 变量中存储的是已有的文件 URL 字符串
        formData.append('workFileUrl', itemData.workFile); // 注意：这里使用了 workFileUrl
    }
  if (itemData.coverImage instanceof File) {
        // 情况 1: 用户上传了新的封面文件
        formData.append('coverImage', itemData.coverImage);
    } else if (typeof itemData.coverImage === 'string' && itemData.coverImage) {
        // 情况 2: 变量中存储的是已有的封面 URL 字符串
        formData.append('coverImageUrl', itemData.coverImage); // 注意：这里使用了 coverImageUrl
    }

  try {
    const response = await createGalleryItem(formData);
    alert('作品创建成功！');
    router.push({ name: 'gallery-item-posts-list', params: { galleryItemId: response.data.id } });
  } catch (err) {
    console.error("创建失败:", err);
    if (isAxiosError(err) && err.response?.status === 403) {
      error.value = "抱歉，只有创作作者才能创建作品。";
    } else {
      error.value = '创建失败，请检查您的输入。';
    }
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
section { margin-bottom: 2.5rem; }
h3 { margin-bottom: 1rem; border-bottom: 1px solid #eee; padding-bottom: 0.5rem; }
.item-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
.item-card { border: 1px solid #eee; padding: 1rem; border-radius: 4px; transition: background-color 0.2s; }
.item-card:hover { background-color: #f9f9f9; }
.item-card a { text-decoration: none; color: inherit; }
.item-card h4 { margin: 0 0 0.5rem 0; }
.loading, .error, .empty-message { color: #888; margin-top: 1rem; }
</style>