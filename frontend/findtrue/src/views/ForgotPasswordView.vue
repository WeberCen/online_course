<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authService } from '@/services/apiService';
import type { PasswordResetRequest, PasswordResetConfirm } from '@/types';

const router = useRouter();
const email = ref('');
const code = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const step = ref(1); // 1: 输入邮箱, 2: 输入验证码和新密码
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const countdown = ref(0);
let countdownInterval: number | null = null;

// 发送验证码
const sendVerificationCode = async () => {
  if (!email.value) {
    errorMessage.value = '请输入邮箱';
    return;
  }

  loading.value = true;
  errorMessage.value = '';

  try {
    const result = await authService.resetPasswordRequest({ email: email.value });
    if (result.success) {
      successMessage.value = '验证码已发送到您的邮箱，请查收';
      startCountdown();
      step.value = 2;
    } else {
      errorMessage.value = result.error || '发送验证码失败，请稍后重试';
    }
  } catch (error) {
    errorMessage.value = '发送验证码过程中发生错误，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 重置密码
const resetPassword = async () => {
  if (!code.value || !newPassword.value || !confirmPassword.value) {
    errorMessage.value = '请填写完整信息';
    return;
  }

  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致';
    return;
  }

  loading.value = true;
  errorMessage.value = '';

  const resetData: PasswordResetConfirm = {
    email: email.value,
    code: code.value,
    newPassword: newPassword.value,
    confirmPassword: confirmPassword.value
  };

  try {
    const result = await authService.resetPasswordConfirm(resetData);
    if (result.success) {
      successMessage.value = '密码重置成功，请使用新密码登录';
      // 重置成功后跳转登录页
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } else {
      errorMessage.value = result.error || '密码重置失败，请稍后重试';
    }
  } catch (error) {
    errorMessage.value = '密码重置过程中发生错误，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 倒计时功能
const startCountdown = () => {
  countdown.value = 60;
  
  if (countdownInterval) {
    clearInterval(countdownInterval);
  }
  
  countdownInterval = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      if (countdownInterval) {
        clearInterval(countdownInterval);
      }
    }
  }, 1000) as unknown as number;
};

// 页面卸载时清除定时器
onUnmounted(() => {
  if (countdownInterval) {
    clearInterval(countdownInterval);
  }
});

const goToLogin = () => {
  router.push('/login');
};
</script>

<template>
  <div class="forgot-password-container">
    <div class="forgot-password-form">
      <h2>忘记密码</h2>
      
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      
      <!-- 第一步：输入邮箱 -->
      <div v-if="step === 1">
        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="请输入您注册时使用的邮箱"
          />
        </div>
        
        <button 
          class="submit-button" 
          @click="sendVerificationCode"
          :disabled="loading"
        >
          {{ loading ? '发送中...' : '发送验证码' }}
        </button>
      </div>
      
      <!-- 第二步：输入验证码和新密码 -->
      <div v-if="step === 2">
        <div class="form-group">
          <label for="code">验证码</label>
          <div class="code-input-group">
            <input
              id="code"
              v-model="code"
              type="text"
              placeholder="请输入验证码"
              maxlength="6"
            />
            <button 
              class="resend-button"
              @click="sendVerificationCode"
              :disabled="countdown > 0 || loading"
            >
              {{ countdown > 0 ? `${countdown}秒后重发` : '重新发送' }}
            </button>
          </div>
        </div>
        
        <div class="form-group">
          <label for="newPassword">新密码</label>
          <input
            id="newPassword"
            v-model="newPassword"
            type="password"
            placeholder="请设置新密码"
          />
        </div>
        
        <div class="form-group">
          <label for="confirmPassword">确认新密码</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
          />
        </div>
        
        <button 
          class="submit-button" 
          @click="resetPassword"
          :disabled="loading"
        >
          {{ loading ? '重置中...' : '重置密码' }}
        </button>
      </div>
      
      <div class="form-footer">
        <button class="link-button" @click="goToLogin">返回登录</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 添加适当的样式 */
.forgot-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #f5f5f5;
}

.forgot-password-form {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.code-input-group {
  display: flex;
  gap: 10px;
}

.code-input-group input {
  flex: 1;
}

.resend-button {
  padding: 10px 15px;
  background-color: #95a5a6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

.resend-button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.error-message {
  color: #e74c3c;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #fadbd8;
  border-radius: 4px;
}

.success-message {
  color: #2ecc71;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #d5f4e6;
  border-radius: 4px;
}

.submit-button {
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

.submit-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.submit-button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.form-footer {
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
</style>