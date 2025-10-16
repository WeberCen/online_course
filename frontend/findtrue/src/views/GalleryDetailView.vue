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
import { 
  getGalleryWorkDetail,
  collectGalleryWork,
  uncollectGalleryWork,
  downloadGalleryWork 
} from '@/services/apiService';
import type { GalleryItemDetail } from '@/types';
import { isAxiosError } from 'axios';

const route = useRoute();
const work = ref<GalleryItemDetail | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const workId = route.params.id as string;

onMounted(async () => {
  if (!workId) {
    error.value = "作品 ID 缺失。";
    loading.value = false;
    return;
  }
  try {
    work.value = await getGalleryWorkDetail(workId);
  } catch (err) {
    console.error("加载作品详情失败:", err);
    if (isAxiosError(err) && err.response?.status === 404) {
      error.value = '找不到指定的作品。';
    } else {
      error.value = '无法加载作品详情。';
    }
  } finally {
    loading.value = false;
  }
});

const handleCollect = async () => {
  if (!work.value) return;
  try {
    await collectGalleryWork(String(work.value.id));
    work.value.is_collected = true;
  } catch (err) {
    console.error("收藏失败:", err);
    if (isAxiosError(err)) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        alert("请先登录再收藏。");
      } else if (err.response?.status === 409) {
        // 如果后端返回冲突，表示已经收藏，同步前端状态
        if (work.value) work.value.is_collected = true;
        alert('您已经收藏了此作品。');
      } else {
        alert("操作失败，请稍后再试。");
      }
    } else {
        alert("发生未知错误，请重试。");
    }
  }
};

const handleUncollect = async () => {
  if (!work.value) return;
  try {
    await uncollectGalleryWork(String(work.value.id));
    work.value.is_collected = false;
  } catch (err) {
    console.error("取消收藏失败:", err);
    if (isAxiosError(err)) {
        if (err.response?.status === 401 || err.response?.status === 403) {
            alert("请先登录。");
        } else {
            alert("操作失败，请稍后再试。");
        }
    } else {
        alert("发生未知错误，请重试。");
    }
  }
};

const handleDownload = async (isConfirmed: boolean = false) => {
  if (!workId) return;

  try {
    const response = await downloadGalleryWork(workId, isConfirmed);
    alert("获取下载链接成功！");
    window.location.href = response.downloadUrl;
    if (work.value) work.value.is_downloaded = true;
  } catch (err) {
    console.error("下载失败:", err);
    if (isAxiosError(err) && err.response) {
      const data = err.response.data as Record<string, unknown> | undefined;

      if (err.response.status === 409 && 
          typeof data === 'object' && data !== null && 
          data.confirmationRequired === true && 
          !isConfirmed) 
      {
        const confirmed = window.confirm(`本次下载需要扣除 ${data.pointsToDeduct} 积分，您确定吗？`);
        if (confirmed) {
          await handleDownload(true);
        }
      } else if (err.response.status === 409 && 
                 typeof data === 'object' && data !== null &&
                 data.prerequisiteNotMet === true) 
      {
        // 安全地存取嵌套屬性
        const requiredWork = data.requiredWork as Record<string, unknown> | undefined;
        const requiredTitle = typeof requiredWork?.title === 'string' ? requiredWork.title : '未知作品';
        alert(`下载失败：您需要先拥有前置作品《${requiredTitle}》。`);
      } else if (err.response.status === 401) {
        alert("请先登录再进行操作。");
      } else if (err.response.status === 402) {
        alert("您的积分不足！");
      } else {
        const detail = (typeof data === 'object' && data !== null && typeof data.detail === 'string') ? data.detail : '未知错误';
        alert(`下载失败: ${detail}`);
      }
    } else {
      alert("下载失败，发生网络或未知错误。");
    }
  }
};
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