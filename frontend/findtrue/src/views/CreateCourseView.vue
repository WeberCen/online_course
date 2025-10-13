<template>
  <div class="create-course-view">
    <h2>创建新课程</h2>
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="title">课程名称</label>
        <input type="text" id="title" v-model="courseData.title" required>
      </div>
      <div class="form-group">
        <label for="description">课程描述</label>
        <RichTextEditor id="description" v-model="courseData.description" rows="5"></RichTextEditor>
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
        <label for="is_vip_free">VIP 免费</label>
      </div>
      
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSubmitting">{{ isSubmitting ? '创建中...' : '创建课程' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { createCourse } from '@/services/apiService';
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue';

const router = useRouter();
const courseData = reactive({
  title: '',
  description: '',
  coverImage: null as String | File | null,
  pricePoints: 0,
  is_vip_free: false,
  tags:[]
});
const isSubmitting = ref(false);
const error = ref<string | null>(null);

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
  if (!courseData.tags.length) {
    error.value = "请添加至少一个标签。";
    isSubmitting.value = false;
    return;
  }
  if (!courseData.description) {
    error.value = "请添加课程描述。";
    isSubmitting.value = false;
    return;
  }
  if (!courseData.title) {
    error.value = "请添加课程名称。";
    isSubmitting.value = false;
    return;
  }
  if (!courseData.pricePoints) {
    error.value = "请添加所需积分。";
    isSubmitting.value = false;
    return;
  }

  const formData = new FormData();
  formData.append('title', courseData.title);
  formData.append('description', courseData.description);
  formData.append('pricePoints', String(courseData.pricePoints));
  formData.append('is_vip_free', String(courseData.is_vip_free));
  if (courseData.coverImage instanceof File) {
        formData.append('coverImage', courseData.coverImage);
    } else if (typeof courseData.coverImage === 'string' && courseData.coverImage) {
        formData.append('coverImageUrl', courseData.coverImage); 
    }

  try {
    const response = await createCourse(formData);
    alert('课程创建成功！初始状态为草稿，请在后台继续编辑章节并提交审核。');
    router.push({ name: 'course-detail', params: { id: response.data.id } });
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