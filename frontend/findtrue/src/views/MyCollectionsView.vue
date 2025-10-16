<template>
  <div class="my-collections-view">
    <h2>我的收藏</h2>
    <div v-if="loading">正在加载...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <section>
        <h3>收藏的课程</h3>
        <div v-if="collections.courses.length > 0" class="item-grid">
          <div v-for="course in collections.courses" :key="course.id" class="item-card">
             <router-link :to="{ name: 'course-detail', params: { id: course.id } }">
               {{ course.title }}
             </router-link>
          </div>
        </div>
        <p v-else>您还没有收藏任何课程。</p>
      </section>
      <section>
        <h3>收藏的作品</h3>
        <div v-if="collections.gallery_items.length > 0" class="item-grid">
          <div v-for="item in collections.gallery_items" :key="item.id" class="item-card">
            <router-link :to="{ name: 'gallery-detail', params: { id: item.id } }">
              {{ item.title }}
            </router-link>
          </div>
        </div>
        <p v-else>您还没有收藏任何画廊作品。</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getMyCollections } from '@/services/apiService';
import type { MyCollections } from '@/types';
import { isAxiosError } from 'axios';

const collections = ref<MyCollections>({ courses: [], gallery_items: [] });
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    // 新模式: 直接等待 API 返回收藏列表數據
    collections.value = await getMyCollections();

  } catch (err) {
    console.error("加载收藏列表失败:", err);
    if (isAxiosError(err)) {
      // 針對未登入的權限錯誤提供特定提示
      if (err.response?.status === 401 || err.response?.status === 403) {
        error.value = '请先登录以查看您的收藏。';
      } else {
        error.value = '加载收藏列表失败，请稍后再试。';
      }
    } else {
      error.value = "加载收藏时发生未知错误。";
    }
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
section { margin-bottom: 2rem; }
.item-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
.item-card { border: 1px solid #eee; padding: 1rem; border-radius: 4px; }
</style>