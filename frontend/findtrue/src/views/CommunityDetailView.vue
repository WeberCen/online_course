<template>
  <div class="community-detail">
    <div v-if="loading">正在加载帖子详情...</div>
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button v-if="error.includes('登入')" @click="goToLogin" class="login-button">
        前往登入
      </button>
    </div>
    <div v-else-if="post">
      <div class="post-main">
        <h1>{{ post.title }}</h1>
        <div class="author-info">
          <span>作者: {{ post.author.nickname || post.author.username }}</span>
          <span>发布于: {{ new Date(post.created_at).toLocaleString() }}</span>
        </div>
        <p class="reward" v-if="post.rewardPoints > 0">悬赏: {{ post.rewardPoints }} 积分</p>
        <div class="post-content" v-html="post.content"></div>
        <div class="actions">
          <button @click="handleLikePost">
            👍 点赞 ({{ postLikesCount }})
          </button>
        </div>
      </div>
      
      <div class="replies-section">
        <h2>{{ post.replies?.length || 0 }} 条回复</h2>
        <div v-for="reply in post.replies" :key="reply.id" class="reply-card">
          <div class="author-info">
            <strong>{{ reply.author.nickname || reply.author.username }}</strong>
            <small>{{ new Date(reply.created_at).toLocaleString() }}</small>
          </div>
          <p>{{ reply.content }}</p>
        </div>
      </div>

      <div class="reply-form">
        <h3>发表你的回复</h3>
        <form @submit.prevent="submitReply">
          <textarea v-model="newReplyContent" rows="5" placeholder="输入你的回复..." required></textarea>
          <button type="submit" :disabled="isReplying">{{ isReplying ? '提交中...' : '提交回复' }}</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getCommunityPostDetail, createCommunityReply, likeCommunityPost } from '@/services/apiService';
import type { CommunityPost, OperationResponse } from '@/types';
import { isAxiosError } from 'axios';

const route = useRoute();
const router = useRouter();
const post = ref<CommunityPost | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const newReplyContent = ref('');
const isReplying = ref(false);

const communityId = route.params.communityId as string;
const postId = route.params.postId as string;

const postLikesCount = computed(() => post.value?.likes?.length || 0);

const fetchPost = async () => {
  if (!communityId || !postId) {
    error.value = "社群或帖子 ID 缺失。";
    loading.value = false;
    return;
  }

  try {
    loading.value = true;
    error.value = null;
    post.value = await getCommunityPostDetail(communityId, postId);
  } catch (err) {
    console.error("加载帖子详情失败:", err);
    if (isAxiosError(err)) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        error.value = '您需要登入才能查看此內容。';
      } else {
        const errorData = err.response?.data;
        let message = err.message;
        if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData && typeof errorData.detail === 'string') {
          message = errorData.detail;
        }
        error.value = `加载帖子失败: ${message}`;
      }
    } else {
      error.value = '加载帖子时发生未知错误。';
    }
  } finally {
    loading.value = false;
  }
};

onMounted(fetchPost);

// --- 修改點 5: 增加跳轉到登入頁的函數 ---
const goToLogin = () => {
  // 可以在跳轉時附帶一個查詢參數，告知登入頁成功後要跳轉回這裡
  router.push({ path: '/login', query: { redirect: route.fullPath } });
};

const submitReply = async () => {
  if (!postId || !newReplyContent.value.trim()) return;
  isReplying.value = true;
  try {
    await createCommunityReply(postId, { content: newReplyContent.value });
    newReplyContent.value = '';
    await fetchPost();
  } catch (err) {
    console.error("回复失败:", err);
    if (isAxiosError(err) && (err.response?.status === 401 || err.response?.status === 403)) {
        alert("请先登录后再回复。");
    } else {
        alert("回复失败，请稍后再试。");
    }
  } finally {
    isReplying.value = false;
  }
};

const handleLikePost = async () => {
  if (!postId) return;
  try {
    const response: OperationResponse = await likeCommunityPost(postId);
    if (response.status) {
        alert(`操作成功: ${response.status}`);
    }
    await fetchPost();
  } catch(err) {
    console.error("点赞/取消点赞失败:", err);
    if (isAxiosError(err) && (err.response?.status === 401 || err.response?.status === 403)) {
      alert("请先登录。");
    } else {
      alert("操作失败，请稍后再试。");
    }
  }
};
</script>

<style scoped>
.post-main { border-bottom: 2px solid #ddd; padding-bottom: 1.5rem; margin-bottom: 1.5rem; }
.author-info { color: #555; font-size: 0.9rem; display: flex; justify-content: space-between; margin: 0.5rem 0; }
.reward { color: #e67e22; font-weight: bold; }
.post-content { margin-top: 1.5rem; line-height: 1.7; }
.actions { margin-top: 1rem; }
.replies-section h2 { margin-bottom: 1rem; }
.reply-card { border: 1px solid #eee; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; }
.reply-form { margin-top: 2rem; }
.reply-form textarea { width: 100%; box-sizing: border-box; padding: 10px; border: 1px solid #ccc; border-radius: 4px; margin-bottom: 1rem; }
</style>