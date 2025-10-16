<template>
  <div class="message-thread-detail-view">
    <div v-if="loading" class="loading">正在加载会话...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="thread">
      <h1>{{ thread.subject }}</h1>
      <div class="messages-container">
        <div v-for="message in thread.messages" :key="message.id" class="message-card">
          <div class="author-info">
            <strong>{{ message.sender.nickname || message.sender.username }}</strong>
            <small>{{ new Date(message.sent_at).toLocaleString() }}</small>
          </div>
          <div class="message-content" v-html="message.content"></div>
        </div>
      </div>
      </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getMessageThreadDetail } from '@/services/apiService';
import type { MessageThreadDetail } from '@/types';
const route = useRoute();
const thread = ref<MessageThreadDetail | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
onMounted(async () => {
  const threadId = route.params.threadId as string;
  try {
    const response = await getMessageThreadDetail(threadId);
    if (response.success) {
      thread.value = response.data;
    } else {
      error.value = response.error || '加载会话内容失败，请稍后再试。';
      console.error('API Error:', response.error);
    }
  } catch (err) {
    error.value = "无法加载会话内容。";
    console.error(err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.conversation-view {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1rem;
}
.messages-container {
  margin-top: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.message-card {
  border: 1px solid #eee;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  background-color: #f9f9f9;
}
.author-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: #555;
}
.message-content {
  line-height: 1.6;
}
/* 样式穿透，美化富文本内容 */
.message-content :deep(p) {
  margin-bottom: 1em;
}
.message-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}
.loading, .error {
  text-align: center;
  padding: 2rem;
  color: #888;
}
</style>