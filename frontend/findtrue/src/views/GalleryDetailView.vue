<template>
  <div class="gallery-detail">
    <div v-if="loading">正在加载作品详情...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="work">
      <h1>{{ work.title }} (v{{ work.version }})</h1>
      <p>作者: {{ work.author.nickname || work.author.username }}</p>
      <img :src="work.coverImage || 'https://via.placeholder.com/800x400'" :alt="work.title + ' 封面'" class="cover-image">
      <div class="description" v-html="work.description"></div>

      <div class="metadata">
        <div class="rating">
          <strong>评分:</strong> {{ work.rating.toFixed(1) }} / 5.0
        </div>
        <div class="tags" v-if="work.tags && work.tags.length > 0">
          <strong>标签:</strong>
          <span v-for="tag in work.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>
      
      <h2>作品描述</h2>
      <p class="description">{{ work.description }}</p>
      
      <div class="actions">
        <button v-if="!work.is_downloaded" @click="handleDownload(false)">下载 ({{ work.requiredPoints }} 积分)</button>
    
        <button v-else @click="handleDownload(true)" class="secondary">重新下载</button>

        <button v-if="!work.is_collected" @click="handleCollect">收藏</button>
        <button v-else @click="handleUncollect" class="secondary">取消收藏</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getGalleryWorkDetail,
  collectGalleryWork,  
  uncollectGalleryWork,
  downloadGalleryWork } from '@/services/apiService';
import type { GalleryItemDetail } from '@/types';
import { isAxiosError } from 'axios';

const route = useRoute();
const work = ref<GalleryItemDetail | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const workId = route.params.id as string;

onMounted(async () => {
  const workId = route.params.id as string;
  try {
    const response = await getGalleryWorkDetail(workId);
    if (response.success) {
      work.value = response.data;
    } else {
      error.value = response.error || '加载作品详情失败，请稍后再试。';
      console.error('API Error:', response.error);
    }
  } catch (err) {
    error.value = '无法加载作品详情。';
    console.error(err);
  } finally {
    loading.value = false;
  }
});
// --- 收藏/取消收藏逻辑 ---
const handleCollect = async () => {
  if (!work.value) return;
  try {
    await collectGalleryWork(String(work.value.id));
    work.value.is_collected = true;
  } catch (err) {
    if (isAxiosError(err) && err.response?.status === 409) {
        work.value.is_collected = true;
        alert('您似乎已经收藏了此作品。');
    } else {
        alert("操作失败，您可能需要重新登录。");
    }
  }
};

const handleUncollect = async () => {
  if (!work.value) return;
  try {
    await uncollectGalleryWork(String(work.value.id));
    work.value.is_collected = false;
  } catch (err) {
    if (isAxiosError(err) && err.response?.status === 409) {
        work.value.is_collected = true;
        alert('您已经取消了收藏。');
    } else {
        alert("操作失败，请重试。");
    }
  }
};

// --- 下载逻辑 (包含二次确认) ---
const handleDownload = async (isConfirmedOrRedownload: boolean = false) => {
  if (!workId) return;

  if (!isConfirmedOrRedownload) {
    // 首次下载，直接调用 API
    try {
      // 直接将参数传递给 API 调用
      const response = await downloadGalleryWork(workId, isConfirmedOrRedownload);
      if (response.success) {
        // 逻辑简化：如果成功，总是处理下载链接
        alert("获取下载链接成功！");
        window.location.href = response.data.downloadUrl;
        if (work.value) work.value.is_downloaded = true;
      } else {
        error.value = response.error || '下载作品失败，请稍后再试。';
        console.error('API Error:', response.error);
      }
    } catch (err) {
      if (isAxiosError(err) && err.response) {
        const data = err.response.data;
        
        // 仅在首次下载（isConfirmedOrRedownload 为 false）时才需要确认
      if (err.response.status === 409 && data.confirmationRequired && !isConfirmedOrRedownload) {
       const confirmed = window.confirm(`本次下载需要扣除 ${data.pointsToDeduct} 积分，您确定吗？`);
         if (confirmed) {
         // 用户确认后，再次调用下载接口，并设置确认参数为 true
          await handleDownload(true); } }
        // 情况二：前置条件未满足
      else if (err.response.status === 409 && data.prerequisiteNotMet) {
        const requiredTitle = data.requiredWork.title;
        alert(`下载失败：您需要先拥有前置作品《${requiredTitle}》。`);
        // 未来我们甚至可以在这里提供一个跳转到该作品页面的链接
      }
        // 其他错误情况
      else if (err.response.status === 401) {
         alert("请先登录再进行操作。");
        }
      else if (err.response.status === 402) {
          alert("您的积分不足！");
        }
      else {alert("下载失败，未知错误。");
        
      }
    } else {
      // 处理非 Axios 错误
      alert("下载失败，发生网络或未知错误。");
      console.error(err);
    }
   }
}};

</script>

<style scoped>
.gallery-detail { 
  max-width: 800px; 
  margin: 2rem auto; 
  font-family: sans-serif;
}
.author-info {
  color: #555;
  margin-top: -10px;
  margin-bottom: 20px;
}
.cover-image { 
  max-width: 100%; 
  height: auto; 
  border-radius: 8px; 
  margin-bottom: 1.5rem; 
}
.metadata {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 8px;
}
.rating {  font-size: 1.1rem;}
.tags {  display: flex;  align-items: center;  gap: 0.5rem;  flex-wrap: wrap;}
.tag {  background-color: #e0e0e0;  padding: 4px 10px;  border-radius: 12px;font-size: 0.9rem;}
.description {  line-height: 1.6;}
.description :deep(p) { margin-bottom: 1em;}
.description :deep(img) { max-width: 100%;  height: auto;  border-radius: 4px;}
.actions {   margin-top: 2rem;}
.actions button {   margin-right: 10px;   padding: 10px 15px;  cursor: pointer;  border: 1px solid #ccc;border-radius: 4px;}
.actions button.secondary { 
  background-color: #eee; 
  color: #333; 
}
</style>