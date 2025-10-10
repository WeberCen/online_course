<template>
  <div>
    <h2>用户登录</h2>
    <form @submit.prevent="handleLogin">
      <div>
        <label for="email">邮箱:</label>
        <input type="email" id="email" v-model="email" required />
      </div>
      <div>
        <label for="password">密码:</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      <button type="submit">登录</button>
    </form>
    <p v-if="message">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';

// 使用 ref 创建响应式变量，用于绑定表单输入
const email = ref('');
const password = ref('');
const message = ref(''); // 用于显示成功或失败的消息

// 处理登录逻辑的异步函数
const handleLogin = async () => {
  message.value = '正在登录...';
  try {
    // 发送 POST 请求到我们的后端登录接口
    const response = await axios.post('http://127.0.0.1:8000/v1/auth/login/', {
      email: email.value,
      password: password.value,
    });

    // 请求成功
    console.log('登录成功，收到 Token:', response.data);
    
    // 将收到的 access token 存储到浏览器的 localStorage 中，以便后续使用
    localStorage.setItem('accessToken', response.data.access);
    
    message.value = '登录成功！Token 已存入 localStorage。';

  } catch (error) {
    // 首先，檢查捕獲到的 error 是否為 Axios 產生的錯誤
    if (axios.isAxiosError(error)) {
      // 在這個 if 判斷內，TypeScript 就會知道 error 是一個 AxiosError 物件
      // 因此可以安全地存取它上面的 .response, .message 等屬性
      console.error('登入失敗 (Axios Error):', error.response ? error.response.data : error.message);

      // 根據後端回傳的具體錯誤訊息，給予使用者更精確的提示
      if (error.response && error.response.data && typeof error.response.data.detail === 'string') {
        message.value = `登入失敗：${error.response.data.detail}`;
      } else {
        message.value = '登入失敗，請檢查信箱或密碼。';
      }

    } else {
      // 如果錯誤不是由 Axios 拋出的（例如，是您程式碼中的其他 bug）
      console.error('發生預期外的錯誤:', error);
      message.value = '發生了一個未知錯誤，請稍後再試。';
    }
  }
};
</script>

<style scoped>
/* 添加一些简单的样式，让表单更好看一点 */
div {
  margin-bottom: 10px;
}
label {
  margin-right: 10px;
}
</style>