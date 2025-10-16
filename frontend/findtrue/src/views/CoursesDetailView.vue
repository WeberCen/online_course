<template>
  <div class="course-detail">
    <div v-if="loading">正在加载课程详情...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else-if="course">
      <h1>{{ course.title }}</h1>
      <p class="author-info">作者: {{ course.author ? (course.author.nickname || course.author.username) : '未知' }}</p>
      <img :src="course.coverImage || 'https://via.placeholder.com/800x400'" alt="Course cover" class="cover-image">
      <div class="description" v-html="course.description"></div>
      
      <div class="actions">
        <button v-if="!course.is_subscribed" @click="handleSubscribe">订阅课程 ({{ course.pricePoints }} 积分)</button>
        <button v-else @click="handleUnsubscribe" class="secondary">取消订阅</button>
        <button v-if="!course.is_collected" @click="handleCollect">收藏</button>
        <button v-else @click="handleUncollect" class="secondary">取消收藏</button>
      </div>

      <div v-if="course.is_subscribed && progress" class="progress-bar">
        <h3>学习进度: {{ progress.completed_exercises }} / {{ progress.total_exercises }} ({{ progress.progress_percentage }}%)</h3>
        <progress :value="progress.completed_exercises" :max="progress.total_exercises"></progress>
        <a v-if="progress.next_chapter_id" :href="`#chapter-${progress.next_chapter_id}`" class="resume-button">
          继续学习
        </a>
      </div>
      
      <h2>章节列表 ({{ course.chapterCount }})</h2>
      <ul>
        <li 
          v-for="chapter in course.chapters" 
          :key="chapter.id"
          :id="`chapter-${chapter.id}`" 
          :class="{ 'current-chapter': progress && chapter.id === progress.nextChapterId }"
          class="chapter-item"
        >
          <div class="chapter-title">
            <strong>{{ chapter.order }}. {{ chapter.title }}</strong>
          </div>
          <video v-if="chapter.videoUrl" :src="chapter.videoUrl" controls width="100%"></video>
          <p v-else-if="course.is_subscribed">[本章暂无视频]</p>
          
          <div v-if="course.is_subscribed && chapter.exercises && chapter.exercises.length > 0" class="exercise-section">
            <h4>章节练习</h4>
            <div v-for="exercise in chapter.exercises" :key="exercise.id" class="exercise">
              <p>{{ exercise.prompt }}</p>
              <div v-if="exercise.type === 'multiple-choice'">
                <div v-for="option in exercise.options" :key="option">
                  <input type="checkbox" :id="`ex${exercise.id}-opt-${option}`" :value="option" v-model="userAnswers[exercise.id]">
                  <label :for="`ex${exercise.id}-opt-${option}`">{{ option }}</label>
                </div>
              </div>
              <div v-if="exercise.type === 'fill-in-the-blank'">
                <input type="text" placeholder="请输入答案" v-model="userAnswers[exercise.id]">
              </div>
            </div>
            <button @click="handleCompleteChapter(chapter.id)" class="complete-btn">提交本章答案</button>
          </div>
        </li>
      </ul>
      <div v-if="!course.is_subscribed && course.chapters.length < course.chapterCount" class="preview-limit">
        <p>... 更多章节内容，订阅后即可查看 ...</p>
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

interface EnhancedExercise extends Exercise {
  options: string[];
}
interface EnhancedChapter extends Chapter {
  exercises: EnhancedExercise[];
}
interface EnhancedCourseDetail extends CourseDetail {
  chapters: EnhancedChapter[];
}

// --- 响应式状态 ---
const route = useRoute();
const course = ref<EnhancedCourseDetail | null>(null);
const progress = ref<Progress | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const userAnswers = reactive<Record<number, string | string[]>>({});
const courseId = route.params.id as string;

// --- 函数 ---
const initializeAnswers = (chapters: EnhancedChapter[]) => {
  for (const chapter of chapters) {
    if (chapter.exercises) {
      for (const exercise of chapter.exercises) {
        userAnswers[exercise.id] = exercise.type === 'multiple-choice' ? [] : '';
      }
    }
  }
};

const fetchPageData = async () => {
  if (!courseId) {
    error.value = '课程ID缺失。';
    loading.value = false;
    return;
  }
  try {
    loading.value = true;
    error.value = null;
    progress.value = null; // 在开始获取数据前，重置进度

    const courseResponse = await getCourseDetail(courseId);
    course.value = courseResponse.data as EnhancedCourseDetail;
    initializeAnswers(course.value.chapters);

    if (localStorage.getItem('accessToken') && course.value?.is_subscribed) {
      try {
        const progressResponse = await getCourseProgress(courseId);
        progress.value = progressResponse.data;
      } catch (progressError) {
        console.warn("无法获取课程进度 (可能是未订阅或其它原因):", progressError);
        // 即使失败，也提供一个默认的进度对象，以避免UI无限加载
        progress.value = {
          completed_exercises: 0,
          total_exercises: course.value?.chapterCount || 0, // 使用章节数作为备用
          progress_percentage: 0,
        };
      }
    } else if (course.value) {
      // 如果用户未订阅，也创建一个默认的进度对象
      progress.value = {
        completed_exercises: 0,
        total_exercises: course.value?.chapterCount || 0,
        progress_percentage: 0,
      };
  } catch (err: unknown) {
    error.value = '无法加载课程数据，请稍后再试。';
    console.error('API Error:', err);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchPageData);

const handleCompleteChapter = async (chapterId: number) => {
  if (!course.value) return;
  const chapter = course.value.chapters.find(c => c.id === chapterId);
  if (!chapter || !chapter.exercises) return;

  const answersToSubmit: ExerciseAnswer[] = [];
  for (const exercise of chapter.exercises) {
    const userAnswer = userAnswers[exercise.id];
    // 只有当用户确实作答了，才提交
    if (userAnswer && (userAnswer.length > 0 || typeof userAnswer === 'string')) {
      answersToSubmit.push({
        exerciseId: exercise.id,
        userAnswer: userAnswer
      });
    }
  }
  
  if (answersToSubmit.length === 0) {
    alert("请至少回答一道题目后再提交。");
    return;
  }

  try {
    await submitChapterExercises(courseId, String(chapterId), answersToSubmit);
    
    // 无论后端返回什么，都刷新数据
    alert('答案已提交！正在刷新学习进度...');
    await fetchPageData();

  } catch (err: unknown) {
    console.error("提交练习失败:", err);
    let alertMessage = "提交失败，未知错误。";
    if (isAxiosError(err)) {
      if (err.response?.status === 500) {
        alertMessage = "服务器暂时无法处理请求，请稍后再试。";
      } else if (err.response?.data) {
        alertMessage = "提交失败: " + JSON.stringify((err.response.data as { error: string }).error || err.response.data);
      }
    }
    alert(alertMessage);
    // 发生错误后也尝试刷新页面数据，以确保状态一致性
    try {
      await fetchPageData();
    } catch (refreshError) {
      console.warn("刷新页面数据失败:", refreshError);
    }
  }
};

const handleSubscribe = async () => {
  if (!course.value) return;
  try {
    await subscribeCourse(String(course.value.id));
    await fetchPageData();
  } catch (err: unknown) {
    console.error("订阅失败:", err);
    if (isAxiosError(err) && err.response?.status === 409) {
      alert('您似乎已经订阅了此课程，正在为您刷新状态...');
      await fetchPageData();
    } else {
      alert("操作失败，您可能需要重新登录。");
    }
  }
};

const handleUnsubscribe = async () => {
  if (!course.value) return;
  const confirmed = window.confirm("您确定要取消订阅吗？积分将不予退还。");
  if (confirmed) {
    try {
      await unsubscribeCourse(String(course.value.id));
      await fetchPageData();
    } catch (err: unknown) {
      console.error("取消订阅失败:", err);
      alert("操作失败，请重试。");
    }
  }
};

const handleCollect = async () => {
  if (!course.value) return;
  try {
    await collectCourse(String(course.value.id));
    course.value.is_collected = true;
  } catch (err: unknown) {
    console.error("收藏失败:", err);
    if (isAxiosError(err) && err.response?.status === 409) {
      course.value.is_collected = true;
      alert('您已经收藏了此课程。');
    } else {
      alert("操作失败，您可能需要重新登录。");
    }
  }
};

const handleUncollect = async () => {
  if (!course.value) return;
  try {
    await uncollectCourse(String(course.value.id));
    course.value.is_collected = false;
  } catch (err: unknown) {
    console.error("取消收藏失败:", err);
    alert("操作失败，请重试。");
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