<template>
  <div class="exercise-manager">
    <button @click="$emit('close')" class="modal-close-btn">×</button>
    <h3>编辑章节与练习</h3>
    
    <div class="chapter-details-form">
      <div class="form-group">
        <label>章节标题</label>
        <input v-model="chapterData.title" />
      </div>
      <div class="form-group">
        <label>视频链接 (Video URL)</label>
        <input v-model="chapterData.videoUrl" type="url" />
      </div>
      <button @click="handleUpdateChapter" :disabled="isSavingChapter">
        {{ isSavingChapter ? '保存中...' : '保存章节信息' }}
      </button>
    </div>

    <hr>

    <h4>练习题管理</h4>
    <div v-if="exercises.length > 0" class="exercise-list">
      <ul>
        <li v-for="exercise in exercises" :key="exercise.id">
          <span class="exercise-type">{{ exercise.type === 'multiple-choice' ? '选择题' : '填空题' }}</span>
          <span class="exercise-prompt">{{ exercise.prompt.substring(0, 50) }}...</span>
          <div class="exercise-actions">
            <button @click="openExerciseForm(exercise)" class="btn-edit">编辑</button>
            <button @click="handleDeleteExercise(exercise)" class="btn-delete">删除</button>
          </div>
        </li>
      </ul>
    </div>
    <p v-else>本章节暂无练习题。</p>
    
    <button @click="openExerciseForm(null)" class="btn-submit">
      添加新练习
    </button>

    <div v-if="editingExercise || isCreatingExercise" class="modal-backdrop-nested">
      <div class="modal-content-nested">
        <ExerciseForm 
          :chapter-id="chapter.id"
          :exercise="editingExercise"
          @close="closeExerciseForm"
          @saved="onExerciseSaved"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import type { PropType } from 'vue';
import type { Chapter, Exercise } from '@/types';
import { updateMyChapter, deleteMyExercise } from '@/services/apiService';
import ExerciseForm from './ExerciseForm.vue';
import { isAxiosError } from 'axios';

const props = defineProps({
  chapter: {
    type: Object as PropType<Chapter>,
    required: true,
  }
});
const emit = defineEmits(['close', 'chapterDataUpdated']);

const chapterData = reactive({
  title: props.chapter.title,
  videoUrl: props.chapter.videoUrl || '',
});
const isSavingChapter = ref(false);
const exercises = ref<Exercise[]>(props.chapter.exercises || []);
const editingExercise = ref<Exercise | null>(null);
const isCreatingExercise = ref(false);

const handleUpdateChapter = async () => {
  isSavingChapter.value = true;
  try {
    await updateMyChapter(String(props.chapter.id), chapterData);
    alert('章节信息已更新。');
    emit('chapterDataUpdated');
  } catch (err) {
    if (isAxiosError(err) && err.response?.data) {
      const errorData = err.response.data;
      if (typeof errorData === 'object' && errorData !== null) {
        alert(`更新失败: ${Object.values(errorData).flat().join(' ')}`);
      } else {
        alert(`更新失败: ${JSON.stringify(errorData)}`);
      }
    } else {
      alert('更新失败，请检查网络连接。');
    }
  }finally {
    isSavingChapter.value = false;
  }
};

const handleDeleteExercise = async (exercise: Exercise) => {
  if (!confirm(`确定要删除此练习题吗？`)) return;
  try {
    await deleteMyExercise(String(exercise.id));
    exercises.value = exercises.value.filter(e => e.id !== exercise.id);
    emit('chapterDataUpdated');
  } catch (err) {
    if (isAxiosError(err) && err.response?.data) {
      alert(`删除失败: ${JSON.stringify(err.response.data)}`);
    } else {
      alert('删除练习失败，请检查网络连接。');
    }
}};

const openExerciseForm = (exercise: Exercise | null) => {
  if (exercise) {
    editingExercise.value = exercise;
    isCreatingExercise.value = false;
  } else {
    editingExercise.value = null;
    isCreatingExercise.value = true;
  }
};

const closeExerciseForm = () => {
  editingExercise.value = null;
  isCreatingExercise.value = false;
};

const onExerciseSaved = () => {
  closeExerciseForm();
  // 通知父组件(CreateChapterManager)刷新所有数据
  emit('chapterDataUpdated'); 
};
</script>

<style scoped>
.exercise-manager { position: relative; }
.modal-close-btn { position: absolute; top: 10px; right: 15px; font-size: 1.5rem; background: none; border: none; cursor: pointer; }
.chapter-details-form { padding-bottom: 15px; border-bottom: 1px solid #eee; }
.exercise-list ul { list-style: none; padding: 0; }
.exercise-list li { display: flex; align-items: center; gap: 8px; padding: 8px; border-bottom: 1px solid #f0f0f0; }
.exercise-type { font-size: 0.8em; background: #eee; padding: 2px 6px; border-radius: 4px; }
.exercise-prompt { flex-grow: 1; }
.modal-backdrop-nested { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1002; display: flex; justify-content: center; align-items: center; }
.modal-content-nested { background: #fff; padding: 20px; border-radius: 8px; width: 90%; max-width: 700px; max-height: 90vh; overflow-y: auto; }
</style>