<template>
  <div class="my-participations-view">
    <h2>我参与的帖子</h2>
    <div v-if="loading" class="loading">正在加载...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="participations.posts.length > 0" class="post-list">
      <div v-for="post in participations.posts" :key="post.id" class="item-card">
        <router-link :to="{ name: 'community-post-detail', params: { communityId: post.community, postId: post.id } }">
          <h4>{{ post.title }}</h4>
          </router-link>
      </div>
    </div>
    <p v-else class="empty-message">您还没有回复过任何帖子。</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getMyParticipations } from '@/services/apiService';
import type { MyParticipations } from '@/types';
import { isAxiosError } from 'axios';

const participations = ref<MyParticipations>({ posts: [] });
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    // 新模式: 直接等待 API 返回您參與的帖子列表數據
    participations.value = await getMyParticipations();

  } catch (err) {
    console.error("加载参与的帖子列表失败:", err);
    if (isAxiosError(err)) {
      // 針對未登入的權限錯誤提供特定提示
      if (err.response?.status === 401 || err.response?.status === 403) {
        error.value = '请先登录以查看您参与的帖子。';
      } else {
        error.value = '加载您参与的帖子列表失败，请稍后再试。';
      }
    } else {
      error.value = "加载时发生未知错误。";
    }
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.post-list { display: flex; flex-direction: column; gap: 1rem; }
.item-card { border: 1px solid #eee; padding: 1rem; border-radius: 4px; transition: background-color 0.2s; }
.item-card:hover { background-color: #f9f9f9; }
.item-card a { text-decoration: none; color: inherit; }
.item-card h4 { margin: 0 0 0.5rem 0; }
.meta { font-size: 0.8rem; color: #666; display: flex; justify-content: space-between; }
.loading, .error, .empty-message { color: #888; margin-top: 1rem; }
</style>