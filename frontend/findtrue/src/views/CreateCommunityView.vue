<template>
  <div class="create-view-container">
    <h2>{{ isEditMode ? '编辑社群' : '创建新社群' }}</h2>
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="name">社群名称</label>
        <input type="text" id="name" v-model="communityData.name" required>
      </div>
      <div class="form-group">
        <label for="description">社群描述</label>
        <RichTextEditor v-model="communityData.description" />
      </div>
      <div class="form-group">
        <label for="coverImage">封面图片</label>
        <input type="file" id="coverImage" @change="handleFileChange" accept="image/*">
      </div>

            <div class="form-group">
        <label for="tags">社群标签</label>
        <input 
          type="text" 
          id="tags" 
          v-model="tagsInput" 
          placeholder="例如: 问答, 官方, 吹水 (用逗号分隔)"
        >
        <div class="tags-preview" v-if="communityData.tags.length">
          <span v-for="tag in communityData.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSubmitting">{{ isSubmitting ? '保存中...' : (isEditMode ? '保存修改' : '创建社群') }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { 
  createMyCommunity, 
  updateMyCommunity, 
  getMyCommunityDetail 
} from '@/services/apiService';
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue';

const router = useRouter();
const route = useRoute();

const communityId = computed(() => route.params.id as string | undefined);
const isEditMode = computed(() => !!communityId.value);

const communityData = reactive({
  name: '',
  description: '',
  coverImage: null as File | null,
  tags: [] as string[],
});

const isSubmitting = ref(false);
const error = ref<string | null>(null);
const tagsInput = ref('');
watch(tagsInput, (newValue) => {
  communityData.tags = newValue.split(',').map(tag => tag.trim());
});



onMounted(async () => {
  if (isEditMode.value && communityId.value) {
    try {
      const data = await getMyCommunityDetail(communityId.value);
      communityData.name = data.name;
      communityData.description = data.description;
      tagsInput.value = data.tags.join(', ');
    } catch (err) {
      console.error("加载社群详情失败:", err);
      if (isAxiosError(err) && err.response?.status === 404) {
        error.value = "找不到指定的社群。";
      } else {
        error.value = '加载社群详情失败，请稍后再试。';
      }
    }
  }
});

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    communityData.coverImage = target.files[0]!;
  } else {
    communityData.coverImage = null;
  }
};

const submitForm = async () => {
  isSubmitting.value = true;
  error.value = null;
  const formData = new FormData();
  formData.append('name', communityData.name);
  formData.append('description', communityData.description);

  if (communityData.coverImage) {
    formData.append('coverImage', communityData.coverImage);
  }
  communityData.tags.forEach(tag => {
    formData.append('tags', tag);
  });

  try {
    if (isEditMode.value && communityId.value) {
      // ** 使用新函数 **
      await updateMyCommunity(communityId.value, formData);
      alert('社群更新成功！');
      router.push({ name: 'community-posts-list', params: { communityId: communityId.value } });
    } else {
      // ** 使用新函数 **
      const newCommunity = await createMyCommunity(formData);
      alert('社群创建成功！');
      router.push({ name: 'community-posts-list', params: { communityId: String(newCommunity.id) } });
    }
  } catch (err) {
    console.error("操作失败:", err);
    if (isAxiosError(err)) {
      if (err.response?.status === 403) {
        error.value = "抱歉，您没有权限执行此操作。";
      } else if (err.response?.data) {
        // 嘗試顯示後端返回的驗證錯誤
        error.value = `操作失败: ${JSON.stringify(err.response.data)}`;
      } else {
        error.value = "操作失败，请检查您的输入或网络连接。";
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
button { padding: 10px 20px; border: none; background-color: #007bff; color: white; border-radius: 4px; cursor: pointer; font-size: 1rem; }
button:disabled { background-color: #a0cffc; }
.error { color: red; margin-bottom: 1rem; }
.tags-preview { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px; }
.tag { background-color: #eee; padding: 2px 8px; border-radius: 12px; font-size: 0.9em; }
</style>