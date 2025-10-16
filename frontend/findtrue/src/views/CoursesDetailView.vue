<template>
  <div class="course-detail">
    <div v-if="loading">正在載入課程詳情...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else-if="course">
      <h1>{{ course.title }}</h1>
      <p class="author-info">作者: {{ course.author ? (course.author.nickname || course.author.username) : '未知' }}</p>
      <img :src="course.coverImage || 'https://via.placeholder.com/800x400'" alt="Course cover" class="cover-image">
      <div class="description" v-html="course.description"></div>
      
      <div class="actions">
        <button v-if="!course.is_subscribed" @click="handleSubscribe">訂閱課程 ({{ course.pricePoints }} 積分)</button>
        <button v-else @click="handleUnsubscribe" class="secondary">取消訂閱</button>
        <button v-if="!course.is_collected" @click="handleCollect">收藏</button>
        <button v-else @click="handleUncollect" class="secondary">取消收藏</button>
      </div>

      <div v-if="course.is_subscribed && progress" class="progress-bar">
        <h3>學習進度: {{ progress.completed_exercises }} / {{ progress.total_exercises }} ({{ progress.progress_percentage }}%)</h3>
        <progress :value="progress.completed_exercises" :max="progress.total_exercises"></progress>
        <a v-if="progress.next_chapter_id" :href="`#chapter-${progress.next_chapter_id}`" class="resume-button">
          繼續學習
        </a>
      </div>
      
      <h2>章節列表 ({{ course.chapterCount }})</h2>
      <ul>
        <li 
          v-for="chapter in course.chapters" 
          :key="chapter.id"
          :id="`chapter-${chapter.id}`" 
          :class="{ 'current-chapter': progress && chapter.id === progress.next_chapter_id }"
          class="chapter-item"
        >
          <div class="chapter-title">
            <strong>{{ chapter.order }}. {{ chapter.title }}</strong>
          </div>
          <video v-if="chapter.videoUrl" :src="chapter.videoUrl" controls width="100%"></video>
          <p v-else-if="course.is_subscribed">[本章暫無影片]</p>
          
          <div v-if="course.is_subscribed && chapter.exercises && chapter.exercises.length > 0" class="exercise-section">
            <h4>章節練習</h4>
            <div v-for="exercise in chapter.exercises" :key="exercise.id" class="exercise">
              <p>{{ exercise.prompt }}</p>
              <div v-if="exercise.type === 'multiple-choice'">
                <div v-for="option in exercise.options" :key="option">
                  <input type="checkbox" :id="`ex${exercise.id}-opt-${option}`" :value="option" v-model="userAnswers[exercise.id]">
                  <label :for="`ex${exercise.id}-opt-${option}`">{{ option }}</label>
                </div>
              </div>
              <div v-if="exercise.type === 'fill-in-the-blank'">
                <input type="text" placeholder="請輸入答案" v-model="userAnswers[exercise.id]">
              </div>
            </div>
            <button @click="handleCompleteChapter(chapter.id)" class="complete-btn">提交本章答案</button>
          </div>
        </li>
      </ul>
      <div v-if="!course.is_subscribed && course.chapters.length < course.chapterCount" class="preview-limit">
        <p>... 更多章節內容，訂閱後即可查看 ...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRoute } from 'vue-router';
import { isAxiosError } from 'axios';
import { 
  getCourseDetail,
  getCourseProgress,
  subscribeCourse,
  unsubscribeCourse,
  collectCourse,
  uncollectCourse,
  submitChapterExercises
} from '@/services/apiService';
import type { CourseDetail, Chapter, Exercise, ExerciseAnswer, Progress } from '@/types';

// --- 類型增強 ---
// 為了在組件中處理 exercises 的選項，我們擴展了原始類型
interface EnhancedExercise extends Exercise {
  options: string[];
}
interface EnhancedChapter extends Chapter {
  exercises: EnhancedExercise[];
}
interface EnhancedCourseDetail extends CourseDetail {
  chapters: EnhancedChapter[];
}

// --- 響應式狀態 ---
const route = useRoute();
const course = ref<EnhancedCourseDetail | null>(null);
const progress = ref<Progress | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const userAnswers = reactive<Record<number, string | string[]>>({});
const courseId = route.params.id as string;

// --- 輔助函式 ---
// 初始化用戶答案的資料結構
const initializeAnswers = (chapters: EnhancedChapter[]) => {
  for (const chapter of chapters) {
    if (chapter.exercises) {
      for (const exercise of chapter.exercises) {
        userAnswers[exercise.id] = exercise.type === 'multiple-choice' ? [] : '';
      }
    }
  }
};

// --- 核心資料獲取邏輯 ---
const fetchPageData = async () => {
  if (!courseId) {
    error.value = '課程ID缺失。';
    loading.value = false;
    return;
  }

  try {
    loading.value = true;
    error.value = null;
    progress.value = null; // 每次刷新都重置進度

    // 1. 獲取課程詳情
    const courseResponse = await getCourseDetail(courseId);

    // 2. 檢查 API 呼叫是否成功 (黃金準則)
    if (courseResponse.success) {
      course.value = courseResponse.data as EnhancedCourseDetail;
      initializeAnswers(course.value.chapters);

      // 3. 檢查用戶是否已登入且已訂閱，以決定是否要獲取進度
      const isLoggedIn = !!localStorage.getItem('accessToken');
      if (isLoggedIn && course.value.is_subscribed) {
        try {
          const progressResponse = await getCourseProgress(courseId);
          if (progressResponse.success) {
            progress.value = progressResponse.data;
          } else {
            console.warn("無法獲取課程進度:", progressResponse.error);
            // 即使獲取進度失敗，也提供一個預設值，避免頁面顯示異常
            progress.value = { completed_exercises: 0, total_exercises: course.value.chapterCount || 0, progress_percentage: 0, next_chapter_id: null };
          }
        } catch (progressError) {
          console.error("獲取課程進度時發生嚴重錯誤:", progressError);
          progress.value = { completed_exercises: 0, total_exercises: course.value.chapterCount || 0, progress_percentage: 0, next_chapter_id: null };
        }
      }
    } else {
      // 如果獲取課程詳情本身就失敗了
      error.value = courseResponse.error || '無法載入課程數據，請稍後再試。';
    }
  } catch (err) {
    // 捕獲網路中斷等更嚴重的錯誤
    error.value = '載入課程時發生網路錯誤，請檢查您的連線。';
    console.error('API Error:', err);
  } finally {
    loading.value = false;
  }
};

// --- 生命週期鉤子 ---
onMounted(fetchPageData);

// --- 事件處理函式 ---
const handleCompleteChapter = async (chapterId: number) => {
  if (!course.value) return;
  const chapter = course.value.chapters.find(c => c.id === chapterId);
  if (!chapter || !chapter.exercises) return;


  const answersToSubmit: ExerciseAnswer[] = []
  for (const exercise of chapter.exercises) {
    const userAnswer = userAnswers[exercise.id];
    if (userAnswer !== undefined && userAnswer !== null && userAnswer.length > 0) {
      answersToSubmit.push({
        exerciseId: exercise.id,
        userAnswer: userAnswer,
      });
    }
  }
  if (answersToSubmit.length === 0) {
    alert("請至少回答一道題目後再提交。");
    return;
  }

  try {
    const response = await submitChapterExercises(courseId, String(chapterId), answersToSubmit);
    if (response.success) {
      alert('答案已提交！正在刷新學習進度...');
      await fetchPageData();
    } else {
      alert(`提交失敗: ${response.error || '未知錯誤'}`);
    }
  } catch (err) {
    console.error("提交練習失敗:", err);
    if (isAxiosError(err) && err.response?.data) {
      alert("提交失敗: " + JSON.stringify(err.response.data));
    } else {
      alert("提交失敗，請檢查網路連線。");
    }
  }
};


const handleSubscribe = async () => {
  if (!course.value) return;
  try {
    await subscribeCourse(String(course.value.id));
    alert('訂閱成功！');
    await fetchPageData(); // 重新載入頁面以更新所有狀態
  } catch (err) {
    console.error("訂閱失敗:", err);
    alert("操作失敗，您可能需要重新登入或檢查您的積分。");
  }
};

const handleUnsubscribe = async () => {
  if (!course.value) return;
  if (window.confirm("您確定要取消訂閱嗎？積分將不予退還。")) {
    try {
      await unsubscribeCourse(String(course.value.id));
      alert('已取消訂閱。');
      await fetchPageData(); // 重新載入頁面
    } catch (err) {
      console.error("取消訂閱失敗:", err);
      alert("操作失敗，請重試。");
    }
  }
};

const handleCollect = async () => {
  if (!course.value) return;
  try {
    await collectCourse(String(course.value.id));
    // 為了更好的用戶體驗，立即更新UI，而不是等待重新載入
    course.value.is_collected = true; 
  } catch (err) {
    console.error("收藏失敗:", err);
    alert("操作失敗，您可能需要重新登入。");
  }
};

const handleUncollect = async () => {
  if (!course.value) return;
  try {
    await uncollectCourse(String(course.value.id));
    course.value.is_collected = false;
  } catch (err) {
    console.error("取消收藏失敗:", err);
    alert("操作失敗，請重試。");
  }
};
</script>

<style scoped>
.course-detail { max-width: 800px; margin: 2rem auto; }
.author-info { color: #555; margin-top: -10px; margin-bottom: 20px; }
.cover-image { max-width: 100%; height: auto; border-radius: 8px; }
.description { line-height: 1.6; }
.description :deep(p) { margin-bottom: 1em;}
.description :deep(img) { max-width: 100%;  height: auto;  border-radius: 4px;}
.actions { margin: 1.5rem 0; display: flex; gap: 1rem; }
.actions button { padding: 10px 15px; cursor: pointer; border: 1px solid #ccc; border-radius: 4px; }
.actions button.secondary { background-color: #eee; color: #333; }
.progress-bar { border: 1px solid #ccc; padding: 1rem; margin: 1rem 0; border-radius: 8px; }
.progress-bar progress { width: 100%; }
.resume-button { display: inline-block; margin-top: 10px; padding: 8px 16px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }
ul { list-style: none; padding: 0; }
.chapter-item { padding: 1rem; border-bottom: 1px solid #eee; }
.current-chapter { background-color: #e7f3ff; border-left: 4px solid #007bff; padding-left: calc(1rem - 4px); }
.chapter-title { font-size: 1.2rem; margin-bottom: 1rem; }
.exercise-section { margin-top: 1.5rem; padding: 1rem; background-color: #f9f9f9; border-radius: 4px; }
.exercise { margin-bottom: 1rem; }
.complete-btn { margin-top: 1rem; }
.preview-limit { text-align: center; color: #888; padding: 2rem; }
.error { color: red; }
</style>