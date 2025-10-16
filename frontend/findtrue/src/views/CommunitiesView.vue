<template>
  <div class="communities-list">
    <h1>社群中心</h1>
    <div v-if="loading">正在加载社群板块...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="community-grid" v-if="communities.length">
      <div v-for="community in communities" :key="community.id" class="community-card">
        <router-link :to="{ name: 'community-posts-list', params: { communityId: community.id } }">
          <img :src="community.coverImage|| 'https://via.placeholder.com/300x120'" alt="Community cover" class="cover-image">
          <div class="card-content">
            <h2>{{ community.name }}</h2>
            <p>{{ community.description }}</p>
            <div class="meta">
              <span>创始人: {{ community.founder.nickname || community.founder.username }}</span>
              <span>帖子数: {{ community.post_count }}</span>
            </div>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getCommunities } from '@/services/apiService'; 
import type { Community } from '@/types';
import { isAxiosError } from 'axios'; // 引入 isAxiosError 用於錯誤判斷

const communities = ref<Community[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    communities.value = await getCommunities();

  } catch (err) {
    console.error("加载社群板块失败:", err); // 打印完整錯誤以供調試

    if (isAxiosError(err)) {
      const errorData = err.response?.data;
      let message = err.message; // 預設使用 Axios 的錯誤訊息
      // 檢查 response.data 中是否有 'detail' 欄位 (Django REST Framework 常用)
      if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData && typeof errorData.detail === 'string') {
        message = errorData.detail;
      }
      error.value = `加载社群失败: ${message}`;
    } else {
      // 處理非網路請求的其他 JS 錯誤
      error.value = '加载社群时发生未知错误，请稍后再试。';
    }
  } finally {
    // 無論成功或失敗，最後都結束加載狀態
    loading.value = false;
  }
});
</script>

<style scoped>
.community-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.5rem; }
.community-card { border: 1px solid #eee; border-radius: 8px; overflow: hidden; transition: box-shadow 0.3s; }
.community-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.community-card a { text-decoration: none; color: inherit; }
.cover-image { width: 100%; height: 120px; object-fit: cover; background-color: #f0f0f0; }
.card-content { padding: 1rem; }
.card-content h2 { margin-top: 0; }
.meta { font-size: 0.9rem; color: #555; display: flex; justify-content: space-between; margin-top: 1rem; border-top: 1px solid #f0f0f0; padding-top: 1rem;}
img {
  max-width: 100%;
  height: auto; }
</style>