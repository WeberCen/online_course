<template>
  <div class="create-message-thread-view">
    <form @submit.prevent="sendMessage">
      <h1>发送新消息</h1>
      <div class="form-group">
        <label for="recipient">收件人 (管理员ID):</label>
        <input id="recipient" type="number" v-model.number="message.recipient_id" required />
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
import { createMessageThread } from '@/services/apiService';
import { isAxiosError } from 'axios';

const router = useRouter();
const message = reactive({ recipient_id: 1, subject: '', content: '' });
const isSending = ref(false);
const error = ref<string | null>(null);

const sendMessage = async () => {
  isSending.value = true;
  error.value = null;
  try {
    await createMessageThread(message);
    alert('发送成功！');
    router.push({ name: 'inbox' });
  } catch (err) {
    console.error("发送失败:", err);
    if (isAxiosError(err) && err.response?.data) {
      error.value = (err.response.data as Record<string, string>).detail || '发送失败，请检查您的输入。';
    } else {
      error.value = '发送失败，请稍后再试。';
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