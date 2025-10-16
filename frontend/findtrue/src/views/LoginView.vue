<template>
  <div class="login-container">
    <div class="login-form-wrapper">
      <h2>登录账号</h2>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="identifier"
            type="text"
            placeholder="请输入用户名"
            required
          />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            required
          />
        </div>
        <div class="form-actions">
          <button type="submit" :disabled="loading" class="btn-login">
            {{ loading ? '登录中...' : '登录' }}
          </button>
          <a @click="goToRegister" class="link-register">没有账号？立即注册</a>
          <a @click="goToForgotPassword" class="link-forgot">忘记密码？</a>
        </div>
      </form>
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authService } from '@/services/apiService';
import type { LoginData } from '@/types';

const router = useRouter();
const identifier = ref(''); // 可以是用户名、邮箱或手机号
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');

const handleLogin = async () => {
  if (!identifier.value || !password.value) {
    errorMessage.value = '请填写完整信息';
    return;
  }

  loading.value = true;
  errorMessage.value = '';

  const loginData: LoginData = {
    identifier: identifier.value,
    password: password.value
  };

  try {
    const result = await authService.login(loginData);
    if (result.success) {
      // 登录成功，跳转到首页
      router.push('/');
    } else {
      errorMessage.value = result.error || '登录失败，请检查您的账号和密码';
    }
  } catch (error) {
    errorMessage.value = '登录过程中发生错误，请稍后重试';
  } finally {
    loading.value = false;
  }
};

const goToRegister = () => {
  router.push('/register');
};

const goToForgotPassword = () => {
  router.push('/forgot-password');
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
}

.login-form-wrapper {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #666;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: #4a90e2;
}

.form-actions {
  margin-top: 24px;
}

.btn-login {
  width: 100%;
  padding: 12px;
  background-color: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-login:hover:not(:disabled) {
  background-color: #357abd;
}

.btn-login:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.link-register,
.link-forgot {
  display: block;
  text-align: center;
  margin-top: 12px;
  color: #4a90e2;
  text-decoration: none;
  font-size: 14px;
}

.link-register:hover,
.link-forgot:hover {
  text-decoration: underline;
}

.error-message {
  margin-top: 16px;
  padding: 12px;
  background-color: #fef0f0;
  color: #f56c6c;
  border-radius: 4px;
  font-size: 14px;
}
</style>