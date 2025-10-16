
<template>
  <div class="register-container">
    <div class="register-form">
      <h2>用户注册</h2>
      
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="username">用户名 *</label>
          <input id="username" v-model="username" type="text" placeholder="请设置用户名" />
        </div>
        <div class="form-group">
          <label for="nickname">昵称</label>
          <input id="nickname" v-model="nickname" type="text" placeholder="请设置昵称（选填）" />
        </div>
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="email">邮箱 *</label>
          <input id="email" v-model="email" type="email" placeholder="请输入邮箱" />
        </div>
        <div class="form-group">
          <label for="phone">手机号 *</label>
          <input id="phone" v-model="phone" type="tel" placeholder="请输入手机号" />
        </div>
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="password">密码 *</label>
          <input id="password" v-model="password" type="password" placeholder="请设置密码" />
        </div>
        <div class="form-group">
          <label for="password2">确认密码 *</label>
          <input id="password2" v-model="password2" type="password" placeholder="请再次输入密码" />
        </div>
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="ageGroup">年龄段</label>
          <select id="ageGroup" v-model="ageGroup">
            <option value="">请选择</option>
            <option value="18-24">18-24岁</option>
            <option value="25-34">25-34岁</option>
            <option value="35-44">35-44岁</option>
            <option value="45+">45岁以上</option>
          </select>
        </div>
        <div class="form-group">
          <label for="gender">性别</label>
          <select id="gender" v-model="gender">
            <option value="">请选择</option>
            <option value="male">男</option>
            <option value="female">女</option>
            <option value="other">其他</option>
          </select>
        </div>
      </div>
      
      <div class="form-group">
        <label for="bio">个人简介</label>
        <textarea id="bio" v-model="bio" placeholder="介绍一下自己吧（选填）" rows="3"></textarea>
      </div>
      
      <button 
        class="register-button" 
        @click="handleRegister"
        :disabled="loading"
      >
        {{ loading ? '注册中...' : '注册' }}
      </button>
      
      <div class="register-footer">
        <span>已有账号？</span>
        <button class="link-button" @click="goToLogin">立即登录</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { isAxiosError } from 'axios';
import { authService } from '@/services/apiService';
import type { RegisterData } from '@/types';

const router = useRouter();
const username = ref('');
const nickname = ref('');
const email = ref('');
const phone = ref('');
const password = ref('');
const password2 = ref('');
const ageGroup = ref('');
const gender = ref('');
const interests = ref<string[]>([]);
const bio = ref('');
const loading = ref(false);
const errorMessage = ref('');

const handleRegister = async () => {
  if (!username.value || !email.value || !phone.value || !password.value || !password2.value) {
    errorMessage.value = '请填写所有必填字段';
    return;
  }
  
  if (password.value !== password2.value) {
    errorMessage.value = '两次输入的密码不一致';
    return;
  }

  loading.value = true;
  errorMessage.value = '';

  const registerData: RegisterData = {
    username: username.value,
    email: email.value,
    phone: phone.value,
    password: password.value,
    password2: password2.value,
    nickname: nickname.value, 
    bio: bio.value,
    gender: gender.value as 'male' | 'female' | 'other' | null,
    ageGroup: ageGroup.value,
    interests: interests.value,
  };

  try {
    // 新模式: 如果註冊成功，API 調用會順利完成
    await authService.register(registerData);
    
    // 成功後的邏輯直接放在這裡
    alert('注册成功，请登录');
    router.push('/login');

  } catch (err) {
    console.error("注册失败:", err);
    if (isAxiosError(err) && err.response?.data) {
      const errorData = err.response.data;
      // 安全地處理後端返回的驗證錯誤（通常是一個物件）
      if (typeof errorData === 'object' && errorData !== null) {
        // 將所有錯誤訊息合併成一個字串顯示給用戶
        errorMessage.value = Object.values(errorData).flat().join(' ');
      } else {
        errorMessage.value = '注册失败，请检查您的输入。';
      }
    } else {
      errorMessage.value = '注册过程中发生未知错误，请检查您的网络连接。';
    }
  } finally {
    loading.value = false;
  }
};

const goToLogin = () => {
  router.push('/login');
};
</script>


<style scoped>
/* 添加适当的样式 */
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #f5f5f5;
}

.register-form {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
}

.form-row {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.form-group {
  flex: 1;
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.error-message {
  color: #e74c3c;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #fadbd8;
  border-radius: 4px;
}

.register-button {
  width: 100%;
  padding: 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.register-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.register-button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.register-footer {
  text-align: center;
  margin-top: 20px;
}

.link-button {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  text-decoration: underline;
}

/* 确保在小屏幕上表单正确显示 */
@media (max-width: 600px) {
  .form-row {
    flex-direction: column;
  }
}
</style>