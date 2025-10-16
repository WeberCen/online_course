<template>
  <div class="my-supported-view">
    <h2>我的已购 / 订阅</h2>
    <div v-if="loading" class="loading">正在加载...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <section>
        <h3>已订阅的课程</h3>
        <div v-if="supported.courses.length > 0" class="item-grid">
          <div v-for="course in supported.courses" :key="course.id" class="item-card">
             <router-link :to="{ name: 'course-detail', params: { id: course.id } }">
               <h4>{{ course.title }}</h4>
             </router-link>
          </div>
        </div>
        <p v-else class="empty-message">您还没有订阅任何课程。</p>
      </section>
      <section>
        <h3>已下载的作品</h3>
        <div v-if="supported.gallery_items.length > 0" class="item-grid">
          <div v-for="item in supported.gallery_items" :key="item.id" class="item-card">
            <router-link :to="{ name: 'gallery-detail', params: { id: item.id } }">
              <h4>{{ item.title }}</h4>
            </router-link>
          </div>
        </div>
        <p v-else class="empty-message">您还没有下载任何画廊作品。</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getMySupported } from '@/services/apiService';
import type { MySupported } from '@/types';
import { isAxiosError } from 'axios';

const supported = ref<MySupported>({ courses: [], gallery_items: [] });
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    // 新模式: 直接等待 API 返回已購列表數據
    supported.value = await getMySupported();

  } catch (err) {
    console.error("加载已购列表失败:", err);
    if (isAxiosError(err)) {
      // 針對未登入的權限錯誤提供特定提示
      if (err.response?.status === 401 || err.response?.status === 403) {
        error.value = '请先登录以查看您的已购列表。';
      } else {
        error.value = '加载您的已购列表失败，请稍后再试。';
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
section { margin-bottom: 2.5rem; }
h3 { margin-bottom: 1rem; border-bottom: 1px solid #eee; padding-bottom: 0.5rem; }
.item-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
.item-card { border: 1px solid #eee; padding: 1rem; border-radius: 4px; transition: background-color 0.2s; }
.item-card:hover { background-color: #f9f9f9; }
.item-card a { text-decoration: none; color: inherit; }
.item-card h4 { margin: 0; }
.loading, .error, .empty-message { color: #888; margin-top: 1rem; }
</style>