<template>
  <div class="create-message-thread-view">
    <form @submit.prevent="sendMessage">
      <h1>发送新消息</h1>
      <div class="form-group">
        <label for="recipient">收件人:</label>
        <input id="recipient" type="text" v-model="recipientSearch" @input="handleSearch" 
          placeholder="输入用户名或昵称进行搜索" required />
        <ul v-if="searchResults.length > 0" class="search-results">
          <li v-for="user in searchResults" :key="user.id" @click="selectRecipient(user)">
            {{ user.nickname || user.username }}
          </li>
        </ul>
      </div>
      <div class="form-group">
        <label for="subject">主题:</label>
        <input id="subject" type="text" v-model="message.subject" required />
      </div>
      <div class="form-group">
        <label for="content">内容:</label>
        <textarea id="content" v-model="message.content" rows="10" required></textarea>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSending">{{ isSending ? '发送中...' : '发送' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { createMessageThread, searchUsers } from '@/services/apiService';
import { isAxiosError } from 'axios';
import type { Author } from '@/types';

const router = useRouter();
const message = reactive({ subject: '', content: '' });
const selectedRecipient = ref<Author | null>(null);
const searchResults = ref<Author[]>([]);
const recipientSearch = ref('');
const isSending = ref(false);
const error = ref<string | null>(null);
let searchTimeout: number | undefined;

const handleSearch = () => {
  clearTimeout(searchTimeout);
  searchResults.value = [];
  selectedRecipient.value = null;

  if (recipientSearch.value.trim().length > 1) {
    searchTimeout = window.setTimeout(async () => {
      try {
        searchResults.value = await searchUsers(recipientSearch.value);
      } catch (err) {
        console.error("用户搜索失败:", err);
        if (isAxiosError(err)) {
          error.value = '搜索用户失败，请稍后再试。';
        } else {
          error.value = '发生未知错误。';
        }
      }
    }, 300);
  }
};

const selectRecipient = (user: Author) => {
  selectedRecipient.value = user;
  recipientSearch.value = user.nickname || user.username;
  searchResults.value = [];
};

const sendMessage = async () => {
  if (!selectedRecipient.value) {
    alert('请从搜索结果中选择一个有效的收件人。');
    return;
  }
  isSending.value = true;
  error.value = null;
  try {
    const payload = {
      ...message,
      recipient_id: selectedRecipient.value.id
    };
    await createMessageThread(payload);
    alert('发送成功！');
    router.push({ name: 'message-inbox' });
  } catch (err) {
    console.error("发送失败:", err);
    if (isAxiosError(err)) {
      const errorData = err.response?.data;
      if (typeof errorData === 'object' && errorData !== null) {
        // 安全地從後端錯誤中提取訊息
        const detail = (errorData as Record<string, unknown>).detail;
        const errorMsg = (errorData as Record<string, unknown>).error;
        error.value = typeof detail === 'string' ? detail : (typeof errorMsg === 'string' ? errorMsg : '发送失败，请检查您的输入。');
      } else {
        error.value = '发送失败，请稍后再试。';
      }
    } else {
      error.value = '发送时发生未知错误。';
    }
  } finally {
    isSending.value = false;
  }
};
</script>

<style scoped>
.compose-view { max-width: 700px; margin: 2rem auto; padding: 1rem; }
.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}
button {
  padding: 10px 20px;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
button:disabled { background-color: #a0cffc; cursor: not-allowed; }
.error { color: red; margin-bottom: 1rem; }
</style>