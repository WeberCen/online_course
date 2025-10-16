<template>
  <div class="create-view-container">
    <h2>{{ isEditMode ? '编辑课程' : '创建新课程' }}</h2>
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="title">课程名称</label>
        <input type="text" id="title" v-model="courseData.title" required>
      </div>

      <div class="form-group">
        <label for="description">课程描述</label>
        <RichTextEditor v-model="courseData.description" />
      </div>

      <div class="form-group">
        <label for="coverImage">课程封面图片</label>
        <input type="file" id="coverImage" @change="handleFileChange" accept="image/*">
      </div>

      <div class="form-group">
        <label for="pricePoints">所需积分</label>
        <input type="number" id="pricePoints" v-model.number="courseData.pricePoints" min="0">
      </div>

      <div class="form-group checkbox-group">
        <input type="checkbox" id="is_vip_free" v-model="courseData.is_vip_free">
        <label for="is_vip_free">此课程对 VIP 免费</label>
      </div>
      
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSubmitting">{{ isSubmitting ? '保存中...' : (isEditMode ? '保存修改' : '创建课程') }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { createCourse, updateCourse, getCourseDetail } from '@/services/apiService';
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue';

const router = useRouter();
const route = useRoute();

// --- 智能表单的核心逻辑 ---
const courseId = computed(() => route.params.id as string | undefined);
const isEditMode = computed(() => !!courseId.value);

const courseData = reactive({
  title: '',
  description: '',
  coverImage: null as File | null,
  pricePoints: 0,
  is_vip_free: false,
});
const isSubmitting = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  if (isEditMode.value && courseId.value) { // 如果是编辑模式...
    try {
      const response = await getCourseDetail(courseId.value); // ...就去后端获取课程数据
      // 将获取到的数据，填充到我们的表单中
      if (response.success) {
        const { title, description, pricePoints, is_vip_free } = response.data;
        courseData.title = title;
        courseData.description = description;
        courseData.pricePoints = pricePoints;
        courseData.is_vip_free = is_vip_free;
      } else {
        error.value = response.error || '加载课程详情失败，请稍后再试。';
        console.error('API Error:', response.error);
      }
    } catch (err) {
    console.error("读取失败:", err);
    if (isAxiosError(err) && err.response?.status === 403) {
      error.value = "读取课程数据失败，请稍后再试。";
    } else {
      error.value = '读取课程数据失败，请检查您的输入。';
    }
  }
  }
});

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    courseData.coverImage = target.files[0]!;
  } else {
    courseData.coverImage = null;
  }
};

const submitForm = async () => {
  isSubmitting.value = true;
  error.value = null;
  const formData = new FormData();
  formData.append('title', courseData.title);
  formData.append('description', courseData.description);
  formData.append('pricePoints', String(courseData.pricePoints));
  formData.append('is_vip_free', String(courseData.is_vip_free));
  if (courseData.coverImage) {
    formData.append('coverImage', courseData.coverImage);
  }

  try {
    let response;
    if (isEditMode.value && courseId.value) {
      response = await updateCourse(courseId.value, formData);
      alert('课程更新成功，已重新提交审核！');
    } else {
      // 创建模式：调用 create API
      response = await createCourse(formData);
      alert('课程创建成功！');
    }
    if (response.success) {
      router.push({ name: 'course-detail', params: { id: String(response.data.id) } });
    } else {
      error.value = response.error || '操作失败，请稍后再试。';
      console.error('API Error:', response.error);
    }
  } catch (err) {
    console.error("创建失败:", err);
    if (isAxiosError(err) && err.response?.status === 403) {
      error.value = "抱歉，只有创作者才能创建课程。";
    } else {
      error.value = '创建失败，请检查您的输入。';
    }
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
section { margin-bottom: 2.5rem; }
h3 { margin-bottom: 1rem; border-bottom: 1px solid #eee; padding-bottom: 0.5rem; }
.item-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
.item-card { border: 1px solid #eee; padding: 1rem; border-radius: 4px; transition: background-color 0.2s; }
.item-card:hover { background-color: #f9f9f9; }
.item-card a { text-decoration: none; color: inherit; }
.item-card h4 { margin: 0 0 0.5rem 0; }
.loading, .error, .empty-message { color: #888; margin-top: 1rem; }
</style>