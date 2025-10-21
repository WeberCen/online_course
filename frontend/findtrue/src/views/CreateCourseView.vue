<template>
  <div class="create-view-container">
    <h2>{{ isEditMode ? '编辑课程' : '创建新课程' }}</h2>
    <div v-if="loading" class="loading-full-page">加载中...</div>
    <form @submit.prevent="submitForm" v-else>
      
      <div class="form-section">
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
          <img v-if="coverImagePreview" :src="coverImagePreview" class="image-preview" alt="封面预览" />
        </div>

              <div class="form-group">
          <label for="tags">课程标签</label>
                  <input 
            type="text" 
            id="tags" 
            v-model="tagsInput" 
            placeholder="例如: Vue, Python (用逗号分隔)"
          >
        </div>

              <div class="form-group">
          <label for="pricePoints">所需积分</label>
          <input type="number" id="pricePoints" v-model.number="courseData.pricePoints" min="0">
        </div>

        <div class="form-group checkbox-group">
          <input type="checkbox" id="is_vip_free" v-model="courseData.is_vip_free">
          <label for="is_vip_free">此课程对 VIP 免费</label>
        </div>
      </div>
      
            <div v-if="error" class="error">{{ error }}</div>
      
      <div class="form-actions">
        <button type="submit" :disabled="isSubmitting" class="btn-save">
          {{ isSubmitting ? '保存中...' : '保存为草稿' }}
        </button>
        
        <button 
          v-if="isEditMode && courseStatus !== 'pending_review'" 
          type="button" 
          @click="handleSubmitForReview" 
          :disabled="isSubmittingReview"
          class="btn-submit"
        >
          {{ isSubmittingReview ? '提交中...' : '提交审核' }}
        </button>
        <p v-if="isEditMode && courseStatus === 'pending_review'" class="status-info">
          (当前状态：审核中... 无法修改)
        </p>
        <p v-if="isEditMode && courseStatus === 'published'" class="status-info">
          (当前状态：已发布)
        </p>
      </div>
    </form>

    <div v-if="isEditMode" class="chapter-manager-section">
      <CreateChapterManager />
    </div>

  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { 
  createMyCourse, 
  updateMyCourse, 
  getMyCourseDetail, 
  submitMyCourseForReview 
} from '@/services/apiService';
import { isAxiosError } from 'axios';
import RichTextEditor from '@/components/RichTextEditor.vue';
import CreateChapterManager from './CreareChapterManager.vue'; 

const router = useRouter();
const route = useRoute();

const courseId = computed(() => route.params.id as string | undefined);
const isEditMode = computed(() => !!courseId.value);
const loading = ref(false);
const courseData = reactive({
  title: '',
  description: '',
  coverImage: null as File | null,
  pricePoints: 0,
  is_vip_free: false,
  tags: [] as string[], 
});
const courseStatus = ref<string | null>(null);
const tagsInput = ref('');
watch(tagsInput, (newVal) => {
  courseData.tags = newVal.split(',').map(t => t.trim()).filter(Boolean);
});
const coverImagePreview = ref<string | null>(null);
const isSubmitting = ref(false);
const isSubmittingReview = ref(false); 
const error = ref<string | null>(null);

onMounted(async () => {
  if (isEditMode.value && courseId.value) {
  loading.value = true;
    try {
      const data = await getMyCourseDetail(courseId.value);
      courseData.title = data.title;
      courseData.description = data.description;
      courseData.pricePoints = data.pricePoints;
      courseData.is_vip_free = data.is_vip_free;
      courseData.tags = data.tags||[]; 
      courseStatus.value = data.status; 
      
      // 回填到简易输入框
      tagsInput.value = (data.tags|| []).join(', ');
      coverImagePreview.value = data.coverImage || null;
      if (data.status === 'pending_review' || data.status === 'published') {
        error.value = "审核中的课程或已发布的课程无法编辑。";
      }
    } catch (err) {
      console.error("加载课程详情失败:", err);
      if (isAxiosError(err) && err.response?.status === 404) {
        error.value = "找不到指定的课程。";
      } else {
        error.value = '加载课程详情失败，请稍后再试。';
      }
    } finally {
      loading.value = false;
    }
  }
});

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    courseData.coverImage = target.files[0]!;
    coverImagePreview.value = URL.createObjectURL(courseData.coverImage);
  } else {
    courseData.coverImage = null;
    coverImagePreview.value = null;
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
  if (courseData.coverImage instanceof File) {
    formData.append('coverImage', courseData.coverImage);
  }
  courseData.tags.forEach(tag => {
    formData.append('tags', tag);
  });

  try {
    if (isEditMode.value && courseId.value) {
      await updateMyCourse(courseId.value, formData);
      alert('课程已保存为草稿！'); 
      courseStatus.value = 'draft'; 
    } else {
      const newCourse = await createMyCourse(formData);
      alert('课程创建成功！现在您可以添加章节了。');
      router.push({ name: 'CreateCourseView', params: { id: String(newCourse.id) } }); 
    }
  } catch (err) {
    console.error("提交表单失败:", err);
    if (isAxiosError(err) && err.response?.data?.error) {
      error.value = err.response.data.error; 
    } else {
      error.value = "提交表单失败，请重试。";
    }
  } finally {
    isSubmitting.value = false;
  }
};

// ** 新增：提交审核的函数 **
const handleSubmitForReview = async () => {
  if (!courseId.value) return;

  isSubmittingReview.value = true;
  error.value = null;
  try {
    const result = await submitMyCourseForReview(courseId.value);
    courseStatus.value = result.status; 
    alert(result.message);
  } catch (err) {
    if (isAxiosError(err) && err.response?.data?.error) {
      error.value = err.response.data.error; 
    } else {
      error.value = "提交审核失败，请重试。";
    }
  } finally {
    isSubmittingReview.value = false;
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
.form-section { border: 1px solid #eee; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
.form-actions { display: flex; gap: 10px; align-items: center; }
.btn-submit { background-color: #4CAF50; color: white; }
.btn-save { background-color: #008CBA; color: white; }
.status-info { color: #888; font-style: italic; }
.image-preview { max-width: 200px; height: auto; margin-top: 10px; border-radius: 4px; }
.chapter-manager-section {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 2px solid #008CBA;
}
</style>