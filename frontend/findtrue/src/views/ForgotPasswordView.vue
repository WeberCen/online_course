<script setup lang="ts">
import { ref ,onUnmounted} from 'vue';
import { useRouter } from 'vue-router';
import { isAxiosError } from 'axios';
import { authService } from '@/services/apiService';
import type { PasswordResetRequest,PasswordResetConfirm } from '@/types';

const router = useRouter();
const code = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const step = ref(1); 
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const countdown = ref(0);
let countdownInterval: number | null = null;
const contactInput = ref('');


const sendVerificationCode = async () => {
  if (!contactInput.value) {
    errorMessage.value = '请输入邮箱或手机号';
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  const isEmail = contactInput.value.includes('@'); 
  const payload: PasswordResetRequest = isEmail 
    ? { email: contactInput.value } 
    : { phone: contactInput.value };


  try {
    const result = await authService.resetPasswordRequest(payload);
    if (result.success) {
      successMessage.value = '驗證碼已發送到您的帳戶，請查收';
      startCountdown();
      step.value = 2;
    } else {
      errorMessage.value = result.error || '發送驗證碼失敗，請稍後重試';
    }
  } catch (error) {
    if (isAxiosError(error) && error.response) {
      errorMessage.value = error.response.data?.detail || error.response.data?.email?.[0] || '發送失敗，請檢查帳號是否正確或稍後再試';
    } else {
      errorMessage.value = '發送驗證碼過程中發生未知錯誤，請檢查網路連接';
    }
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 重置密码
const resetPassword = async () => {
  if (!code.value || !newPassword.value || !confirmPassword.value) {
    errorMessage.value = '請填寫完整資訊';
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = '兩次輸入的密碼不一致';
    return;
  }

  loading.value = true;
  errorMessage.value = '';

  // 2. 【已修正】只聲明一次 resetData，並根據條件構建
  let resetData: PasswordResetConfirm;
  const isEmail = contactInput.value.includes('@');

  const baseData = {
    code: code.value,
    password: newPassword.value,
    password2: confirmPassword.value,
  };

  if (isEmail) {
    resetData = { ...baseData, email: contactInput.value };
  } else {
    resetData = { ...baseData, phone: contactInput.value };
  }
  
  // 3. 執行 API 請求
  try {
    const result = await authService.resetPasswordConfirm(resetData);
    if (result.success) {
      successMessage.value = '密碼重置成功，請使用新密碼登入';
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } else {
      errorMessage.value = result.error || '密碼重置失敗，請稍後重試';
    }
  } catch (error) {
    if (isAxiosError(error) && error.response) {
      errorMessage.value = error.response.data?.detail || error.response.data?.code?.[0] || '密碼重置失敗，請檢查驗證碼或新密碼';
    } else {
      errorMessage.value = '密碼重置過程中發生未知錯誤，請檢查網路連接';
    }
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 倒計時功能
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

// 頁面卸載時清除定時器
onUnmounted(() => {
  if (countdownInterval) {
    clearInterval(countdownInterval);
  }
});
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
          <label for="email">邮箱/ 手机号</label>
          <input
            id="contact"
            v-model="contactInput" type="text" placeholder="请输入您的邮箱或手机号"
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
      
    </div>
  </div>
</template>

<style scoped>
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