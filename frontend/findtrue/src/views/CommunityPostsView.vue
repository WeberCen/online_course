<template>
  <div class="community-posts-list">
    <div class="header">
      <h1>帖子列表</h1>
      <router-link :to="{ name: 'create-post', params: { communityId: communityId } }" class="create-post-btn">
        发布新帖
      </router-link>
    </div>
    <div v-if="loading">正在加载帖子...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="post-list" v-if="posts.length">
      <div v-for="post in posts" :key="post.id" class="post-card">
        <router-link :to="{ name: 'community-post-detail', params: { communityId: communityId, postId: post.id } }">
          <h2>{{ post.title }}</h2>
          <p v-if="post.rewardPoints > 0" class="reward">悬赏: {{ post.rewardPoints }} 积分</p>
          <div class="meta">
            <span>作者: {{ post.author.nickname || post.author.username }}</span>
            <span>回复: {{ post.reply_count }}</span>
            <span class="time">{{ new Date(post.created_at).toLocaleString() }}</span>
          </div>
        </router-link>
      </div>
    </div>
    <div v-else-if="!loading">
      <p>这个社群还没有帖子，快来发布第一篇吧！</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getPostsForCommunity } from '@/services/apiService';
import type { CommunityPostListItem } from '@/types';

const route = useRoute();
const posts = ref<CommunityPostListItem[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const communityId = route.params.communityId as string;

onMounted(async () => {
  if (!communityId) {
    error.value = "社群 ID 缺失。";
    loading.value = false;
    return;
  }
  try {
    const response = await getPostsForCommunity(communityId);
    posts.value = response.data;
  } catch (err) {
    error.value = '无法加载帖子列表，请稍后再试。';
    console.error(err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.create-post-btn { background-color: #007bff; color: white; padding: 10px 15px; border-radius: 4px; text-decoration: none; font-weight: bold; }
.post-card { border: 1px solid #eee; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; }
.post-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.post-card a { text-decoration: none; color: inherit; }
.reward { color: #e67e22; font-weight: bold; font-size: 0.9rem; }
.meta { font-size: 0.9rem; color: #555; display: flex; gap: 1.5rem; margin-top: 1rem; }
</style>
