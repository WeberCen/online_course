<template>
  <div class="message-inbox-view">
    <div class="header">
      <h1>我的消息</h1>
      <router-link :to="{ name: 'compose-message' }" class="compose-btn">写新消息</router-link>
    </div>
    <div v-if="loading" class="loading">正在加载消息列表...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="threads.length > 0" class="thread-list">
      <div v-for="thread in threads" :key="thread.id" class="thread-item">
        <router-link :to="{ name: 'conversation-detail', params: { id: thread.id } }" class="thread-link">
          <div class="thread-info">
            <strong class="subject">{{ thread.subject }}</strong>
            <p v-if="thread.last_message" class="last-message">
              {{ thread.last_message.content.replace(/<[^>]*>/g, '').substring(0, 70) }}...
            </p>
            <p v-else class="last-message">还没有消息。</p>
          </div>
          <div class="thread-meta">
            <small>{{ new Date(thread.created_at).toLocaleString() }}</small>
          </div>
        </router-link>
      </div>
    </div>
    <p v-else class="empty-message">您的收件箱是空的。</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getMessageThreads } from '@/services/apiService';
import type { MessageThread } from '@/types';
const threads = ref<MessageThread[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    const response = await getMessageThreads();
    threads.value = response.data;
  } catch (err) {
    error.value = "无法加载消息列表，请稍后再试。";
    console.error(err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.inbox-view {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1rem;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}
.compose-btn {
  background-color: #007bff;
  color: white;
  padding: 10px 15px;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
}
.thread-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.thread-item {
  border: 1px solid #eee;
  border-radius: 8px;
  transition: box-shadow 0.2s;
}
.thread-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.thread-link {
  display: flex;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  text-decoration: none;
  color: inherit;
}
.subject {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  display: block;
}
.last-message {
  font-size: 0.9rem;
  color: #555;
  margin: 0;
}
.thread-meta {
  font-size: 0.8rem;
  color: #888;
  white-space: nowrap;
  margin-left: 1rem;
}
.loading, .error, .empty-message {
  text-align: center;
  padding: 2rem;
  color: #888;
}
</style>