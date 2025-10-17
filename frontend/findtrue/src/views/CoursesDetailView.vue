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
              
              <div v-if="userSubmissions[exercise.id]" class="review-mode">
                <p v-html="exercise.prompt" class="prompt-done"></p>
                <div class="review-area">
                  <p>
                    <strong>你的答案:</strong> {{ userSubmissions[exercise.id]?.user_answer }}
                    <span v-if="userSubmissions[exercise.id]?.is_correct" class="correct-badge">✓ 正確</span>
                    <span v-else class="incorrect-badge">✗ 錯誤</span>
                  </p>
                  
                  <div v-if="showAnalysis[exercise.id]" class="analysis">
                    <p><strong>正確答案:</strong> {{ userSubmissions[exercise.id]?.correct_answer }}</p>
                    <p><strong>解析:</strong> {{ userSubmissions[exercise.id]?.analysis }}</p>
                  </div>

                  <div class="review-actions">
                     <button @click="toggleAnalysis(exercise.id)" class="secondary-btn">
                      {{ showAnalysis[exercise.id] ? '隱藏解析' : '答案解析' }}
                    </button>
                  </div>
                </div>
              </div>

              <div v-else class="answering-mode">
                <p v-html="exercise.prompt"></p>
                <div v-if="exercise.type === 'multiple-choice'">
                  <div v-for="option in exercise.options" :key="option.id">
                    <input type="checkbox" :id="`ex${exercise.id}-opt-${option.id}`" :value="option.text" v-model="userAnswers[exercise.id]">
                    <label :for="`ex${exercise.id}-opt-${option.id}`">{{ option.text }}</label>
                  </div>
                </div>
                <div v-if="exercise.type === 'fill-in-the-blank'">
                  <input type="text" placeholder="請輸入答案" v-model="userAnswers[exercise.id]">
                </div>
              </div>
            </div>

            <div class="chapter-actions">
                <button @click="handleCompleteChapter(chapter.id)">提交本章答案</button>
                <button @click="redoChapter(chapter)" class="secondary-btn">重做本章</button>
            </div>
          </div>
          </li>
      </ul>

      <div v-if="!course.is_subscribed && course.chapters.length < course.chapterCount" class="preview-limit">
        <p>... 更多章節內容，訂閱後即可查看 ...</p>
      </div>
    </div>

    <div v-if="submissionReportForPopup" class="modal-overlay" @click="closeResultsPopup">
      <div class="modal-content" @click.stop>
        <h3>批改結果</h3>
        <p class="summary">
          答對 <strong>{{ submissionReportForPopup.summary.correct_count }}</strong> 題，
          答錯 <strong>{{ submissionReportForPopup.summary.incorrect_count }}</strong> 題。
        </p>
        <div v-if="submissionReportForPopup.summary.incorrect_count > 0" class="incorrect-list">
          <h4>回答錯誤的題目：</h4>
          <ul>
            <li v-for="ex in submissionReportForPopup.summary.incorrect_exercises" :key="ex.id">
              <p v-html="ex.prompt"></p>
            </li>
          </ul>
        </div>
        <button @click="closeResultsPopup">我知道了</button>
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
import type { CourseDetail, Chapter, 
  ExerciseAnswer, Progress,UserSubmission,
  SubmissionReport} from '@/types';

// --- 響應式狀態 (保持不變) ---
const route = useRoute();
const course = ref<CourseDetail | null>(null);
const progress = ref<Progress | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const userAnswers = reactive<Record<number, string | string[]>>({});
const userSubmissions = ref<Record<number, UserSubmission>>({});
const submissionReportForPopup = ref<SubmissionReport | null>(null);
const showAnalysis = ref<Record<number, boolean>>({});
const courseId = route.params.id as string;

// --- 輔助函式 (保持不變) ---
const initializeAnswers = (chapters: Chapter[]) => {
  for (const chapter of chapters) {
    if (chapter.exercises) {
      for (const exercise of chapter.exercises) {
        // 如果後端返回了歷史提交記錄 (進入複習模式)
        if (exercise.user_submission) {
          userSubmissions.value[exercise.id] = exercise.user_submission;
          // 將用戶上次的答案填入表單模型，方便複習模式下展示
          userAnswers[exercise.id] = exercise.user_submission.user_answer;
        } else {
          // 否則，正常初始化為空 (進入答題模式)
          userAnswers[exercise.id] = exercise.type === 'multiple-choice' ? [] : '';
        }
      }
    }
  }
};

const fetchPageData = async () => {
  if (!courseId) {
    error.value = '課程ID缺失。';
    loading.value = false;
    return;
  }

  loading.value = true;
  error.value = null;
  userSubmissions.value = {}; // 每次刷新前清空舊的提交記錄

  try {
    const courseData = await getCourseDetail(courseId);
    course.value = courseData;
    
    // 使用升級後的初始化函數
    initializeAnswers(course.value.chapters);

    const isLoggedIn = !!localStorage.getItem('accessToken');
    if (isLoggedIn && course.value.is_subscribed) {
      try {
        progress.value = await getCourseProgress(courseId);
      } catch (progressError) {
        console.warn("無法獲取課程進度:", progressError);
        progress.value = null;
      }
    }
  } catch (err) {
    console.error('載入課程核心數據時發生錯誤:', err);
    if (isAxiosError(err)) {
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



// --- 3. 提交邏輯升級 ---
const handleCompleteChapter = async (chapterId: number) => {
  if (!course.value) return;
  const chapter = course.value.chapters.find(c => c.id === chapterId);
  if (!chapter || !chapter.exercises) return;

  // 篩選出用戶實際作答的題目
  const answersToSubmit: ExerciseAnswer[] = chapter.exercises.reduce((acc, exercise) => {
    // 只處理未做過的題目
    if (!userSubmissions.value[exercise.id]) {
      const userAnswer = userAnswers[exercise.id];
      if (userAnswer !== undefined && userAnswer !== null && String(userAnswer).length > 0) {
        acc.push({
          exerciseId: exercise.id,
          userAnswer: userAnswer, // 在此上下文中，類型是正確的
        });
      }
    }
    return acc;
  }, [] as ExerciseAnswer[]);

  if (answersToSubmit.length === 0) {
    alert("您尚未作答任何新題目。");
    return;
  }

  try {
    const report = await submitChapterExercises(String(chapterId), answersToSubmit);
    // 將返回的報告存起來，用於觸發彈窗
    submissionReportForPopup.value = report;
    // 提交成功後，立即刷新整個頁面的數據，以獲取最新的 user_submission 狀態
    await fetchPageData();
  } catch (err) {
    console.error("提交練習失敗:", err);
    if (isAxiosError(err)) {
      const errorData = err.response?.data;
      let errorDetail = '未知伺服器錯誤';
      if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData && typeof errorData.detail === 'string') {
        errorDetail = errorData.detail;
      }
      alert(`提交失敗: ${errorDetail}`);
    } else {
      alert("提交失敗，請檢查網路連線。");
    }
  }
};

// --- 4. 新增輔助函數 ---
const redoChapter = (chapter: Chapter) => {
  if (!chapter.exercises) return;
  if (!window.confirm("確定要重做本章所有練習嗎？這將會清除您本章的作答記錄。")) return;

  for (const exercise of chapter.exercises) {
    delete userSubmissions.value[exercise.id];
    // 重置答案模型
    userAnswers[exercise.id] = exercise.type === 'multiple-choice' ? [] : '';
  }
  // 可選：調用後端 API 來刪除數據庫記錄
};

const toggleAnalysis = (exerciseId: number) => {
  showAnalysis.value[exerciseId] = !showAnalysis.value[exerciseId];
};

const closeResultsPopup = () => {
  submissionReportForPopup.value = null;
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