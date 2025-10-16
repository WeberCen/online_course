<template>
  <div class="my-profile-view">
    <h2>个人信息</h2>
    <div v-if="loading" class="loading">正在加载您的信息...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <form v-else-if="user" @submit.prevent="updateProfile">
      <div class="info-section">
        <h3>账户信息</h3>
        <div class="form-group">
          <label>用户名:</label>
          <p class="readonly-field">{{ user.username }}</p>
        </div>
        <div class="form-group">
          <label>邮箱:</label>
          <p class="readonly-field">{{ user.email }}</p>
        </div>
        <div class="form-group">
          <label>手机号:</label>
          <p class="readonly-field">{{ user.phone }}</p>
        </div>
        <div class="form-group">
          <label>当前角色:</label>
          <p class="readonly-field">{{ user.role }}</p>
        </div>
        <div class="form-group">
          <label>VIP 到期时间:</label>
          <p class="readonly-field">{{ user.vip_expiration_date ? new Date(user.vip_expiration_date).toLocaleDateString() : '非VIP用户' }}</p>
        </div>
        <div class="form-group">
          <label>当前积分:</label>
          <p class="readonly-field">{{ user.currentPoints }}</p>
        </div>
      </div>
      
      <hr>

      <div class="edit-section">
        <h3>编辑个人资料</h3>
        <div class="form-group">
          <label for="nickname">昵称:</label>
          <input id="nickname" type="text" v-model="editableProfile.nickname">
        </div>

        <div class="form-group">
          <label for="bio">个人介绍:</label>
          <RichTextEditor v-model="editableProfile.bio" />
        </div>

        <div class="form-group">
          <label for="gender">性别:</label>
          <select id="gender" v-model="editableProfile.gender">
            <option value="男">男</option>
            <option value="女">女</option>
            <option value="不想告知">不想告知</option>
          </select>
        </div>

        <div class="form-group">
          <label for="ageGroup">年龄段:</label>
          <select id="ageGroup" v-model="editableProfile.ageGroup">
            <option value="小学">小学</option>
            <option value="初中">初中</option>
            <option value="高中">高中</option>
            <option value="成人">成人</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>兴趣标签 (可多选):</label>
          <div class="interests-group">
            <div v-for="interest in allInterests" :key="interest" class="interest-item">
              <input type="checkbox" :id="`interest-${interest}`" :value="interest" v-model="editableProfile.interests">
              <label :for="`interest-${interest}`">{{ interest }}</label>
            </div>
          </div>
        </div>
        
        <button type="submit" :disabled="isSaving">{{ isSaving ? '保存中...' : '保存修改' }}</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { getMyProfile, updateMyProfile } from '@/services/apiService';
import type { User, UserProfileUpdatePayload } from '@/types'; // 从 @/types 导入
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue'; // 导入富文本编辑器

const user = ref<User | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const isSaving = ref(false);

// 创建一个独立的响应式对象来绑定表单
const editableProfile = reactive<UserProfileUpdatePayload>({
  nickname: '',
  bio: '', // 新增
  gender: null,
  ageGroup: null,
  interests: [],
});

const allInterests = ['代码学习', '思维训练', '游戏开发', '网页爬虫', '智能体调用'];

onMounted(async () => {
  try {
    const response = await getMyProfile();
    if (response.success) {
      user.value = response.data;
    
    // 将获取到的数据同步到可编辑对象中
    editableProfile.nickname = response.data.nickname;
    editableProfile.bio = response.data.bio; 
    editableProfile.gender = response.data.gender;
    editableProfile.ageGroup = response.data.ageGroup;
    editableProfile.interests = response.data.interests || [];
  } else{
    error.value = response.error || "無法加載您的個人信息。";
    console.error('API Error:', response.error);
    }
  }catch (err) {
    error.value = "无法加载您的个人信息，请稍后重试。";
    console.error(err);
  } finally {
    loading.value = false;
  }
});

const updateProfile = async () => {
  isSaving.value = true;
  try {
    const response = await updateMyProfile(editableProfile);
    if (response.success) {
      user.value = response.data; 

    alert('个人信息更新成功！');
  } else {
      // 處理業務邏輯上的失敗（例如，暱稱已被佔用）
      alert(`更新失敗: ${response.error || '未知錯誤'}`);
    }
  }catch (err) {
    console.error("更新失败:", err);
    if (isAxiosError(err) && err.response?.data) {
      alert("更新失败: " + JSON.stringify(err.response.data));
    } else {
      alert("更新失败，请稍后再试。");
    }
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.my-profile-view { max-width: 700px; }
.info-section, .edit-section {
  padding: 1.5rem;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 2rem;
}
h2, h3 {
  margin-top: 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #eee;
}
.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
.readonly-field { font-size: 1rem; padding: 10px; background-color: #f4f4f4; border-radius: 4px; color: #555; }
hr { display: none; }
.interests-group { display: flex; flex-wrap: wrap; gap: 1rem; }
.interest-item { display: flex; align-items: center; }
.interest-item input { width: auto; margin-right: 0.5rem; }
button { padding: 12px 25px; border: none; background-color: #007bff; color: white; border-radius: 4px; cursor: pointer; font-size: 1rem; }
button:disabled { background-color: #a0cffc; cursor: not-allowed; }
.loading, .error { color: #888; margin-top: 1rem; }
</style>