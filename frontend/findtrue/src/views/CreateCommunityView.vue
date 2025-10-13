<template>
  <div class="create-community-view">
    <h2>创建新社群</h2>
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="name">社群名称</label>
        <input type="text" id="name" v-model="communityData.name" required>
      </div>
      <div class="form-group">
        <label for="description">社群描述</label>
        <RichTextEditor id="description" v-model="communityData.description" rows="5"></RichTextEditor>
      </div>
       <div class="form-group">
        <label for="coverImage">封面图片</label>
        <input type="file" id="coverImage" @change="handleFileChange" accept="image/*">
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSubmitting">{{ isSubmitting ? '创建中...' : '创建社群' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { createCommunity } from '@/services/apiService';
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue';

const router = useRouter();
const communityData = reactive({
  name: '',
  description: '',
  coverImage: null as String | File | null,
  tags: [],
});
const isSubmitting = ref(false);
const error = ref<string | null>(null);

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    communityData.coverImage = target.files[0]!;
  } else {
    communityData.coverImage = null;
  }
};

const submitForm = async () => {
    if (!communityData.name) {
        alert("请添加社群名称。");
        return;
    }
    if (!communityData.description) {
        alert("请添加社群描述。");
        return;
    }
    if (!communityData.coverImage) {
        alert("请添加社群封面图片。");
        return;
    }
    if (!communityData.tags.length) {
        alert("请添加至少一个标签。");
        return;
    }
  isSubmitting.value = true;
  error.value = null;

  const formData = new FormData();
  formData.append('name', communityData.name);
  formData.append('description', communityData.description);
  formData.append('tags', communityData.tags.join(','));
  if (communityData.coverImage instanceof File) {
        // 情况 1: 用户上传了新的封面文件
        formData.append('coverImage', communityData.coverImage);
    } else if (typeof communityData.coverImage === 'string' && communityData.coverImage) {
        // 情况 2: 变量中存储的是已有的封面 URL 字符串
        formData.append('coverImageUrl', communityData.coverImage); // 注意：这里使用了 coverImageUrl
    }

  try {
    const response = await createCommunity(formData);
    alert('社群创建成功！');
    router.push({ name: 'community-posts-list', params: { communityId: response.data.id } });
  } catch (err) {
    console.error("创建失败:", err);
    if (isAxiosError(err) && err.response?.status === 403) {
      error.value = "抱歉，只有创作者才能创建社群。";
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