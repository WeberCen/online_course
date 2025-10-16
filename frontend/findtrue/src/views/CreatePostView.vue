<template>
  <div class="create-post-view">
    <h1>发布新帖子</h1>
    <form @submit.prevent="submitPost">
      <div class="form-group">
        <label for="title">标题</label>
        <input type="text" id="title" v-model="post.title" required>
      </div>
      <div class="form-group">
        <label for="content">内容</label>
        <RichTextEditor id="content" v-model="post.content" rows="10" required></RichTextEditor>
      </div>
      <div class="form-group">
        <label for="reward">悬赏积分 (可选)</label>
        <input type="number" id="reward" v-model.number="post.rewardPoints" min="0">
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? '发布中...' : '发布帖子' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createCommunityPost } from '@/services/apiService';
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue';

const route = useRoute();
const router = useRouter();
const communityId = route.params.communityId as string;

const post = reactive({ title: '', content: '', rewardPoints: 0 });
const isSubmitting = ref(false);
const error = ref<string | null>(null);

const submitPost = async () => {
  if (!communityId) {
    error.value = "社群 ID 丢失，无法发布。";
    return;
  }
  isSubmitting.value = true;
  error.value = null;
  try {
    const response = await createCommunityPost(communityId, post);
    if (response.success) {
      router.push({ name: 'community-post-detail', params: { communityId: communityId, postId: String(response.data.id) } });
    } else {
      error.value = response.error || '发布失败，请稍后再试。';
      console.error('API Error:', response.error);
    }
  } catch (err) {
    console.error("发帖失败:", err);
    if (isAxiosError(err) && err.response?.data) {
      error.value = (err.response.data as { error: string }).error || '发布失败，请检查您的输入或积分。';
    } else {
      error.value = '发布失败，请稍后再试。';
    }
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.create-post-view { max-width: 700px; margin: 2rem auto; }
.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}
button {
  padding: 10px 20px;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
button:disabled { background-color: #a0cffc; }
.error { color: red; margin-bottom: 1rem; }
</style>