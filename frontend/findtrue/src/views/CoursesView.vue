<template>
  <div class="courses-list">
    <h1>所有课程</h1>
    <div v-if="loading">正在加载课程...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="course-grid" v-if="courses.length">
      <div v-for="course in courses" :key="course.id" class="course-card">
        <router-link :to="{ name: 'course-detail', params: { id: course.id } }">
          <img :src="course.coverImage || 'https://via.placeholder.com/300x150'" alt="Course cover">
          <div class="card-content">
            <h2>{{ course.title }}</h2>
            <p>{{ course.description ? course.description.substring(0, 100) + '...' : '暂无描述' }}</p>
            <div class="author">
              <span>作者: {{ course.author ? (course.author.nickname || course.author.username) : '未知' }}</span>
            </div>
          </div>
        </router-link>
      </div>
    </div>
    <div v-else-if="!loading">
      <p>目前还没有已发布的课程。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getCourses } from '@/services/apiService';
import type { Course } from '@/types';

const courses = ref<Course[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    const response = await getCourses();
    courses.value = response.data;
  } catch (err) {
    error.value = '无法加载课程，请稍后再试。';
    console.error(err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.courses-list {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
}
.course-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
  gap: 1.5rem; 
}
.course-card { 
  border: 1px solid #ddd; 
  border-radius: 8px; 
  overflow: hidden; 
  transition: box-shadow 0.3s;
}
.course-card:hover { 
  box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
}
.course-card a {
  text-decoration: none;
  color: inherit;
}
.course-card img { 
  width: 100%; 
  height: 150px; 
  object-fit: cover; 
  background-color: #f0f0f0;
}
.card-content {
  padding: 1rem;
}
.card-content h2 {
  margin-top: 0;
  font-size: 1.2rem;
}
.card-content p {
  font-size: 0.9rem;
  color: #555;
  min-height: 50px; /* 保证卡片高度基本一致 */
}
.author { 
  font-size: 0.9rem; 
  color: #555; 
  padding-top: 0.5rem;
  margin-top: 1rem;
  border-top: 1px solid #f0f0f0;
}
.error {
  color: red;
}
</style>