<template>
  <div class="my-creations-view">
    <div class="header">
      <h2>我的创作</h2>
    </div>

    <div v-if="loading" class="loading">正在加载您的创作...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <section>
        <div class="section-header">
          <h3>我创建的课程</h3>
          <router-link :to="{ name: 'create-course' }" class="create-btn">+ 创建新课程</router-link>
        </div>
        <div v-if="creations.courses.length > 0" class="item-grid">
          <div v-for="course in creations.courses" :key="course.id" class="item-card">
            <router-link :to="{ name: 'course-detail', params: { id: course.id } }">
              <h4>{{ course.title }}</h4>
              <p>状态: {{ course.status }}</p>
            </router-link>
            <div class="card-actions">
              <router-link :to="{ name: 'edit-course', params: { id: course.id } }" class="edit-btn">编辑</router-link>
            </div>
          </div>
        </div>
        <p v-else class="empty-message">您还没有创建任何课程。</p>
      </section>

      <section>
        <div class="section-header">
          <h3>我发布的画廊作品</h3>
          <router-link :to="{ name: 'create-gallery-item' }" class="create-btn">+ 上传新作品</router-link>
        </div>
        <div v-if="creations.gallery_items.length > 0" class="item-grid">
          <div v-for="item in creations.gallery_items" :key="item.id" class="item-card">
            <router-link :to="{ name: 'gallery-detail', params: { id: item.id } }">
              <h4>{{ item.title }}</h4>
              <p>版本: v{{ item.version }}</p>
            </router-link>
            <div class="card-actions">
              <router-link :to="{ name: 'edit-gallery-item', params: { id: item.id } }" class="edit-btn">编辑</router-link>
            </div>
          </div>
        </div>
        <p v-else class="empty-message">您还没有发布任何画廊作品。</p>
      </section>

      <section>
        <div class="section-header">
          <h3>我创建的社群</h3>
          <router-link :to="{ name: 'create-community' }" class="create-btn">+ 创建新社群</router-link>
        </div>
        <div v-if="creations.founded_communities.length > 0" class="item-grid">
          <div v-for="community in creations.founded_communities" :key="community.id" class="item-card">
            <router-link :to="{ name: 'community-posts-list', params: { communityId: community.id } }">
              <h4>{{ community.name }}</h4>
              <p>帖子数: {{ community.post_count }}</p>
            </router-link>
            <div class="card-actions">
              <router-link :to="{ name: 'edit-community', params: { id: community.id } }" class="edit-btn">编辑</router-link>
            </div>
          </div>
        </div>
        <p v-else class="empty-message">您还没有创建任何社群。</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getMyCreations } from '@/services/apiService';
import type { MyCreations } from '@/types';


const creations = ref<MyCreations>({ 
  courses: [], gallery_items: [], founded_communities: [] });
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    const response = await getMyCreations();
    creations.value = response.data;
  } catch (err) {
    error.value = "无法加载您的创作列表。";
    console.error(err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}
.header h2 { margin: 0; }

section { margin-bottom: 2.5rem; }
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
.section-header h3 { margin: 0; }
.create-btn {
  background-color: #007bff;
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
}

.item-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
.item-card {
  border: 1px solid #eee;
  padding: 1rem;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.item-card a { text-decoration: none; color: inherit; }
.item-card h4 { margin: 0 0 0.5rem 0; }
.card-actions {
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f0f0f0;
  text-align: right;
}
.edit-btn {
  font-size: 0.8rem;
  padding: 4px 10px;
  border-radius: 4px;
  background-color: #6c757d;
  color: white;
  text-decoration: none;
}
.loading, .error, .empty-message { color: #888; margin-top: 1rem; }
</style>