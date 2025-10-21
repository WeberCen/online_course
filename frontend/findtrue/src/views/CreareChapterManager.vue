<template>
  <div class="chapter-manager">
    <h3>
      课程章节管理
      <span v-if="loading" class="spinner"> (加载中...)</span>
    </h3>
    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="chapters.length > 0">
      <ol class="chapter-list">
        <li v-for="(chapter, index) in chapters" :key="chapter.id" class="chapter-item">
          
          <div class="chapter-order-controls">
            <button 
              @click="moveChapter(index, -1)" 
              :disabled="index === 0 || isSavingOrder"
              title="上移"
            >
              ↑
            </button>
            <button 
              @click="moveChapter(index, 1)" 
              :disabled="index === chapters.length - 1 || isSavingOrder"
              title="下移"
            >
              ↓
            </button>
          </div>

          <span class="chapter-title">{{ chapter.title }}</span>

          <div class="chapter-actions">
            <button type="button" @click="openExerciseManager(chapter)" class="btn-edit">
              编辑章节 / 练习 ({{ chapter.exercises?.length || 0 }})
            </button>
            <button type="button" @click="handleDeleteChapter(chapter)" class="btn-delete">删除</button>
          </div>
        </li>
      </ol>
      <p v-if="isSavingOrder" class="status-info">正在保存顺序...</p>
    </div>
    <p v-else-if="!loading">暂无章节，请在下方添加。</p>

    <form @submit.prevent="handleCreateChapter" class="add-chapter-form">
      <h4>添加新章节</h4>
      <div class="form-group">
        <label>章节标题</label>
        <input v-model="newChapter.title" placeholder="例如：章节一：环境配置" required />
      </div>
      <div class="form-group">
        <label>视频链接 (Video URL)</label>
        <input v-model="newChapter.videoUrl" placeholder="https://..." type="url" />
      </div>
      <button type="submit" :disabled="isSubmittingCreate">
        {{ isSubmittingCreate ? '添加中...' : '添加章节' }}
      </button>
    </form>

    <div v-if="editingChapter" class="modal-backdrop">
      <div class="modal-content">
        <CreateExerciseManager 
          :chapter="editingChapter"
          @close="editingChapter = null"
          @chapterDataUpdated="refreshCourseData" 
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRoute } from 'vue-router';
import { 
  getMyCourseDetail, 
  createMyChapter, 
  deleteMyChapter, 
  updateMyChapterOrder 
} from '@/services/apiService';
import type { Chapter } from '@/types';
import CreateExerciseManager from './CreateExerciseManager.vue';
import { isAxiosError } from 'axios';

const route = useRoute();
const courseId = route.params.id as string;

const chapters = ref<Chapter[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const isSubmittingCreate = ref(false); 
const isSavingOrder = ref(false); 

const newChapter = reactive({
  title: '',
  videoUrl: '',
});

const editingChapter = ref<Chapter | null>(null);

const fetchChapters = async () => {
  loading.value = true;
  error.value = null;
  try {
    const course = await getMyCourseDetail(courseId);
    chapters.value = (course.chapters || []).sort((a, b) => a.order - b.order);
  } catch (err) {
    console.error("加载章节失败:", err);
    error.value = "加载章节数据失败，请刷新页面。";
  } finally {
    loading.value = false;
  }
};

onMounted(fetchChapters);

const moveChapter = async (index: number, direction: -1 | 1) => {
  const newIndex = index + direction;
  // 边界检查
  if (newIndex < 0 || newIndex >= chapters.value.length) return;

  isSavingOrder.value = true;
  
  // 1. 在前端数组中交换
  const list = [...chapters.value];
  const [movedItem] = list.splice(index, 1);
  if (movedItem) {
    list.splice(newIndex, 0, movedItem);
  }
  chapters.value = list;

  // 2. 提交新顺序到后端
  try {
    const chapterIds = chapters.value.map(c => String(c.id));
    await updateMyChapterOrder(courseId, chapterIds);
  } catch (err) {
    if (isAxiosError(err) && err.response?.status === 400) {
      alert('顺序更新失败，可能是因为章节顺序已被其他用户修改。请刷新页面重试。');
    } else {
      alert('顺序更新失败，将重新加载。');
    }
    await fetchChapters(); // 出错时回滚
  } finally {
    isSavingOrder.value = false;
  }
};

// 3. 创建新章节
const handleCreateChapter = async () => {
  isSubmittingCreate.value = true;
  try {
    const created = await createMyChapter(courseId, {
      title: newChapter.title,
      videoUrl: newChapter.videoUrl,
    });
    created.exercises = [];
    // 刷新整个列表以获取正确的顺序
    await fetchChapters();
    newChapter.title = '';
    newChapter.videoUrl = '';
  } catch (err) {
    if (isAxiosError(err) && err.response?.status === 400) {
      alert('创建章节失败，可能是因为标题已存在。请重试。');
    } else {
      alert('创建章节失败，请重试。');
    }
  } finally {
    isSubmittingCreate.value = false;
  }
};

// 4. 删除章节
const handleDeleteChapter = async (chapterToDelete: Chapter) => {
  if (!confirm(`确定要删除章节 "${chapterToDelete.title}" 吗？`)) return;
  try {
    await deleteMyChapter(String(chapterToDelete.id));
    chapters.value = chapters.value.filter(c => c.id !== chapterToDelete.id);
  } catch (err) {
    if (isAxiosError(err) && err.response?.status === 400) {
      alert('删除失败，可能是因为章节已被其他用户使用。请刷新页面重试。');
    } else {
      alert('删除失败，请重试。');
    }
  }
};

// 5. 打开练习管理器
const openExerciseManager = (chapter: Chapter) => {
  editingChapter.value = chapter;
};

// 6. 刷新数据
const refreshCourseData = () => {
  editingChapter.value = null;
  fetchChapters();
};
</script>

<style scoped>
.chapter-list {
  list-style: none;
  padding: 0;
}
.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border: 1px solid #ccc;
  margin-bottom: 5px;
}
</style>