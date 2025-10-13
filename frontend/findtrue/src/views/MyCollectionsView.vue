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

const collections = ref<MyCollections>({ courses: [], gallery_items: [] });
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    const response = await getMyCollections();
    collections.value = response.data;
  } catch (err) {
    error.value = "无法加载收藏列表。";
    console.error(err);
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