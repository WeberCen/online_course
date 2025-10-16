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
  if (isEditMode.value && courseId.value) {
    try {
      const data = await getCourseDetail(courseId.value);
      courseData.title = data.title;
      courseData.description = data.description;
      courseData.pricePoints = data.pricePoints;
      courseData.is_vip_free = data.is_vip_free;
    } catch (err) {
      console.error("加载课程详情失败:", err);
      if (isAxiosError(err) && err.response?.status === 404) {
        error.value = "找不到指定的课程。";
      } else {
        error.value = '加载课程详情失败，请稍后再试。';
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
    if (isEditMode.value && courseId.value) {
      const updatedCourse = await updateCourse(courseId.value, formData);
      alert('课程更新成功，已重新提交审核！');
      router.push({ name: 'course-detail', params: { id: String(updatedCourse.id) } });
    } else {
      const newCourse = await createCourse(formData);
      alert('课程创建成功！');
      router.push({ name: 'course-detail', params: { id: String(newCourse.id) } });
    }
  } catch (err) {
    console.error("操作失败:", err);
    if (isAxiosError(err)) {
      if (err.response?.status === 403) {
        error.value = "抱歉，您没有权限执行此操作。";
      } else {
        const errorData = err.response?.data;
        // 安全地處理後端驗證錯誤，避免使用 any
        if (typeof errorData === 'object' && errorData !== null) {
          error.value = `操作失败: ${Object.values(errorData).flat().join(' ')}`;
        } else {
          error.value = "操作失败，请检查您的输入或网络连接。";
        }
      }
    } else {
      error.value = '发生未知错误，请重试。';
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