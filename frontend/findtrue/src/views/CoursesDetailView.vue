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
            <p v-html="exercise.prompt"></p>
            <div v-if="exercise.type === 'multiple-choice'">     
              <div v-for="option in exercise.options" :key="option.id">
                <input 
                  type="checkbox" 
                  :id="`ex${exercise.id}-opt-${option.id}`" 
                  :value="option.text"  
                  v-model="userAnswers[exercise.id]"
                >
             <label :for="`ex${exercise.id}-opt-${option.id}`">{{ option.text }}</label>
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
import type { CourseDetail, Chapter, ExerciseAnswer, Progress} from '@/types';

/* --- 類型增強  ---

interface EnhancedExercise extends Exercise {
  options: ExerciseOption[];
}
interface EnhancedChapter extends Chapter {
  exercises: EnhancedExercise[];
}
interface EnhancedCourseDetail extends CourseDetail {
  chapters: EnhancedChapter[];
}
*/
// --- 響應式狀態 (保持不變) ---
const route = useRoute();
const course = ref<CourseDetail | null>(null);
//const course = ref<EnhancedCourseDetail | null>(null);
const progress = ref<Progress | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const userAnswers = reactive<Record<number, string | string[]>>({});
const courseId = route.params.id as string;

// --- 輔助函式 (保持不變) ---
const initializeAnswers = (chapters: Chapter[]) => {
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

  loading.value = true;
  error.value = null;

  try {
    // 1. 獲取課程詳情
    // 新模式: 直接接收數據，如果失敗會在此處拋出錯誤並進入 catch 塊
    const courseData = await getCourseDetail(courseId);
    course.value = courseData;
    
    initializeAnswers(course.value.chapters);

    // 2. 檢查用戶是否已登入且已訂閱，以決定是否要獲取進度
    const isLoggedIn = !!localStorage.getItem('accessToken');
    if (isLoggedIn && course.value.is_subscribed) {
      try {
        // 同樣，直接獲取進度數據
        progress.value = await getCourseProgress(courseId);
      } catch (progressError) {
        // 如果只是獲取進度失敗，我們不讓整個頁面崩潰，只在控制台警告
        console.warn("無法獲取課程進度:", progressError);
        progress.value = null; // 或者設置一個預設值
      }
    }
  } catch (err) {
    // 這個 catch 會捕獲 getCourseDetail 的失敗
    console.error('載入課程核心數據時發生錯誤:', err);
    if (isAxiosError(err)) {
      // 安全地處理錯誤訊息
      const errorData = err.response?.data as Record<string, unknown>;
      const detail = typeof errorData?.detail === 'string' ? errorData.detail : err.message;
      error.value = `無法載入課程：${detail}`;
    } else {
      error.value = '載入課程時發生未知錯誤，請稍後再試。';
    }
  } finally {
    loading.value = false;
  }
};

// --- 生命週期鉤子 (保持不變) ---
onMounted(fetchPageData);

// --- 事件處理函式 ---
const handleCompleteChapter = async (chapterId: number) => {
  if (!course.value) return;
  const chapter = course.value.chapters.find(c => c.id === chapterId);
  if (!chapter || !chapter.exercises) return;

  const answersToSubmit: ExerciseAnswer[] = chapter.exercises.reduce((acc, exercise) => {
    const userAnswer = userAnswers[exercise.id];
    // 檢查答案是否有效 (非 undefined, null, 或空字串)
    if (userAnswer !== undefined && userAnswer !== null && String(userAnswer).length > 0) {
      acc.push({
        exerciseId: exercise.id,
        userAnswer: userAnswer, 
      });
    }
    return acc;
  }, [] as ExerciseAnswer[]);

  if (answersToSubmit.length === 0) {
    alert("請至少回答一道題目後再提交。");
    return;
  }

  try {
    await submitChapterExercises(courseId, String(chapterId), answersToSubmit);
    alert('答案已提交！正在刷新學習進度...');
    await fetchPageData();
  } catch (err) {
    console.error("提交練習失敗:", err);
    if (isAxiosError(err)) {
      const errorData = err.response?.data;
      let errorDetail = "未知伺服器錯誤";
      if (typeof errorData === 'object' && errorData !== null) {
        const data = errorData as Record<string, unknown>;
        if (typeof data.detail === 'string') {
          errorDetail = data.detail;
        } else {
          errorDetail = JSON.stringify(data);
        }
      }
      alert(`提交失敗: ${errorDetail}`);
    } else {
      alert("提交失敗，請檢查網路連線。");
    }
  }
};

const handleSubscribe = async () => {
  if (!course.value) return;
  const confirmationMessage = `訂閱該課程將扣除 ${course.value.pricePoints} 積分，您確定嗎？`;
  if (window.confirm(confirmationMessage)) {
    try {
      await subscribeCourse(String(course.value.id));
      alert('訂閱成功！');
      await fetchPageData(); 
    } catch (err) {
      console.error("訂閱失敗:", err);
      if (isAxiosError(err)) {
        if (err.response && (err.response.status === 401 || err.response.status === 403)) {
          alert("請先登入後再訂閱課程。");
        } else {
          const errorData = err.response?.data;
          let errorDetail = "您可能積分不足或發生其他錯誤。";
          if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData && typeof errorData.detail === 'string') {
            errorDetail = errorData.detail;
          }
          alert(`操作失敗: ${errorDetail}`);
        }
      } else {
        alert("發生未知的錯誤，請重試。");
      }
    }
  }
};


const handleUnsubscribe = async () => {
  if (!course.value) return;
  if (window.confirm("您確定要取消訂閱嗎？積分將不予退還。")) {
    try {
      await unsubscribeCourse(String(course.value.id));
      alert('已取消訂閱。');
      await fetchPageData(); 
    } catch (err) {
      console.error("取消訂閱失敗:", err);
      if (isAxiosError(err)) {
        if (err.response && (err.response.status === 401 || err.response.status === 403)) {
          alert("請先登入。");
        } else {
          alert("操作失敗，請重試。");
        }
      } else {
        alert("發生未知的錯誤，請重試。");
      }
    }
  }
};

const handleCollect = async () => {
  if (!course.value) return;
  try {
    await collectCourse(String(course.value.id));
    alert('感謝支持，收藏成功');
    course.value.is_collected = true; 
  } catch (err) {
    console.error("收藏失敗:", err);
    if (isAxiosError(err)) {
      if (err.response && (err.response.status === 401 || err.response.status === 403)) {
        alert("請先登入後再收藏。");
      } else {
        const errorData = err.response?.data;
        let errorDetail = "請稍後重試。";
        if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData && typeof errorData.detail === 'string') {
          errorDetail = errorData.detail;
        }
        alert(`操作失敗: ${errorDetail}`);
      }
    } else {
      alert("發生未知的錯誤，請重試。");
    }
  }
};

const handleUncollect = async () => {
  if (!course.value) return;
  if (window.confirm("您確定要取消收藏嗎？")) {

    try {
      await uncollectCourse(String(course.value.id));
      course.value.is_collected = false;
    } catch (err) {
      console.error("取消收藏失敗:", err);
      if (isAxiosError(err)) {
        if (err.response && (err.response.status === 401 || err.response.status === 403)) {
          alert("請先登入。");
        } else {
          alert("操作失敗，請重試。");
        }
      } else {
        alert("發生未知的錯誤，請重試。");}
    }
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