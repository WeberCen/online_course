<template>
  <div class="gallery-list">
    <h1>画廊作品</h1>
    <div v-if="loading">正在加载...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="work-grid" v-if="works.length">
      <div v-for="work in works" :key="work.id" class="work-card">
        <router-link :to="{ name: 'gallery-detail', params: { id: work.id } }">
          <img :src="work.coverImage || 'https://via.placeholder.com/300x200'" :alt="work.title + ' 封面'">
          <h2>{{ work.title }}</h2>
          <p>v{{ work.version }}</p>
          <div class="author">
            <span>作者: {{ work.author.nickname || work.author.username }}</span>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getGalleryWorks } from '@/services/apiService';
import type { GalleryItem } from '@/types';
import { isAxiosError } from 'axios';

const works = ref<GalleryItem[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    // 新模式: 直接等待 API 返回畫廊作品列表數據
    works.value = await getGalleryWorks();

  } catch (err) {
    console.error("加载画廊作品失败:", err);
    if (isAxiosError(err)) {
      // 嘗試從後端響應中獲取更具體的錯誤訊息
      const errorData = err.response?.data;
      let message = err.message;
      if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData && typeof errorData.detail === 'string') {
        message = errorData.detail;
      }
      error.value = `加载作品失败: ${message}`;
    } else {
      error.value = '加载作品时发生未知错误，请稍后再试。';
    }
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.work-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
.work-card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
.work-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.work-card a { text-decoration: none; color: inherit; }
.work-card img { width: 100%; height: 200px; object-fit: cover; }
.work-card h2, .work-card p, .author { padding: 0 1rem; }
.author { font-size: 0.9rem; color: #555; padding-bottom: 1rem; }
</style>