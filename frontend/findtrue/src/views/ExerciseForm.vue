<template>
  <div class="exercise-form">
    <button @click="$emit('close')" class="modal-close-btn">×</button>
    <h3>{{ isEditMode ? '编辑练习题' : '创建新练习题' }}</h3>

    <div v-if="loading" class="loading">加载练习题详情...</div>
    
    <form @submit.prevent="submitForm" v-else>
      <div class="form-group">
        <label for="type">题目类型</label>
        <select id="type" v-model="form.type" :disabled="isEditMode">
          <option value="multiple-choice">多选题</option>
          <option value="fill-in-the-blank">填空题</option>
        </select>
        <p v-if="isEditMode" class="field-help">（编辑时无法修改题目类型）</p>
      </div>

      <div class="form-group">
        <label for="prompt">题干</label>
        <RichTextEditor v-model="form.prompt" />
      </div>
      
      <div class="form-group">
        <label for="explanation">答案解析 (可选)</label>
        <RichTextEditor v-model="form.explanation" />
      </div>

      <div class="form-group">
        <label for="image_upload">配图 (可选)</label>
        <input type="file" @change="handleFileChange" accept="image/*" />
        <img v-if="imagePreview" :src="imagePreview" class="image-preview" />
      </div>

      <div v-if="form.type === 'multiple-choice'" class="dynamic-form-section">
        <h4>选项</h4>
        <div v-for="(option, index) in options" :key="index" class="option-item">
          <input type="text" v-model="option.text" placeholder="选项内容" required />
          <div class="checkbox-group">
            <input type="checkbox" :id="`is_correct_${index}`" v-model="option.is_correct" />
            <label :for="`is_correct_${index}`">正确答案</label>
          </div>
          <button typeD="button" @click="removeOption(index)" :disabled="options.length <= 1">移除</button>
        </div>
        <button type="button" @click="addOption">添加选项</button>
      </div>

      <div v-if="form.type === 'fill-in-the-blank'" class="dynamic-form-section">
        <h4>答案</h4>
        <div v-for="(blank, index) in blanks" :key="index" class="blank-item">
          <input type="text" v-model="blank.correct_answer" placeholder="填空答案" required />
          <input type="number" v-model.number="blank.index_number" min="1" title="答案序号" />
          <div class="checkbox-group">
            <input type="checkbox" :id="`case_sensitive_${index}`" v-model="blank.case_sensitive" />
            <label :for="`case_sensitive_${index}`">区分大小写</label>
          </div>
          <button type="button" @click="removeBlank(index)" :disabled="blanks.length <= 1">移除</button>
        </div>
        <button type="button" @click="addBlank">添加答案</button>
      </div>
      
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="isSubmitting" class="btn-submit">
        {{ isSubmitting ? '保存中...' : '保存练习' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import type { PropType } from 'vue';
import type { Exercise } from '@/types';
import { createMyExercise, updateMyExercise, getMyExerciseDetail } from '@/services/apiService';
import RichTextEditor from '@/components/RichTextEditor.vue';
import { isAxiosError } from 'axios';


interface CreatorOption {
  id?: number | string;
  text: string;
  is_correct: boolean;
}

interface CreatorFillInBlank {
  id?: number | string;
  index_number: number;
  correct_answer: string;
  case_sensitive: boolean;
}

interface CreatorExercise {
  id: number | string;
  type: 'multiple-choice' | 'fill-in-the-blank';
  prompt: string;
  explanation?: string | null;
  image_url?: string | null;
  image_upload?: string | null;
  
  // 关键：使用我们本地的、完整的类型
  options?: CreatorOption[];
  fill_in_blanks?: CreatorFillInBlank[];
}
const props = defineProps({
  chapterId: {
    type: [String, Number],
    required: true,
  },
  exercise: {
    type: Object as PropType<Exercise | null>,
    default: null,
  }
});
const emit = defineEmits(['close', 'saved']);

const isEditMode = computed(() => !!props.exercise);
const loading = ref(false);
const isSubmitting = ref(false);
const error = ref<string | null>(null);

const form = reactive({
  type: 'multiple-choice' as 'multiple-choice' | 'fill-in-the-blank',
  prompt: '',
  explanation: '',
  image_upload: null as File | null,
});
const imagePreview = ref<string | null>(null);

const options = ref<Partial<CreatorOption>[]>([{ text: '', is_correct: false }]);
const blanks = ref<Partial<CreatorFillInBlank>[]>([{ index_number: 1, correct_answer: '', case_sensitive: false }]);

onMounted(async () => {
  if (isEditMode.value && props.exercise) {
    loading.value = true;
    try {
      const data = await getMyExerciseDetail(String(props.exercise.id)) as unknown as CreatorExercise;

      form.type = data.type;
      form.prompt = data.prompt;
      form.explanation = data.explanation || '';
      imagePreview.value = data.image_url || data.image_upload || null;
      
      // 报错消失：TypeScript 知道 data 上有 'fill_in_blanks'
      if (data.type === 'fill-in-the-blank' && data.fill_in_blanks?.length) {
        blanks.value = data.fill_in_blanks;
      }
      
      // 报错消失：TypeScript 知道 data.options 是 CreatorOption[]
      if (data.type === 'multiple-choice' && data.options?.length) {
        options.value = data.options;
      }
    } catch (err) {
    console.error("练习题保存失败:", err);
    if (isAxiosError(err) && err.response?.data) {
      const errors = err.response.data;
      if (typeof errors === 'object') {
        error.value = `保存失败: ${Object.values(errors).flat().join(' ')}`;
      } else {
        error.value = `保存失败: ${JSON.stringify(errors)}`;
      }
    } else {
      error.value = "保存失败，请重试。";
    }
  } finally {
    isSubmitting.value = false;
  }
}});


const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    form.image_upload = target.files[0]!;
    imagePreview.value = URL.createObjectURL(form.image_upload);
  } else {
    form.image_upload = null;
  }
};

const addOption = () => options.value.push({ text: '', is_correct: false });
const removeOption = (index: number) => options.value.splice(index, 1);
const addBlank = () => blanks.value.push({ index_number: blanks.value.length + 1, correct_answer: '', case_sensitive: false });
const removeBlank = (index: number) => blanks.value.splice(index, 1);

const submitForm = async () => {
  isSubmitting.value = true;
  error.value = null;
  
  const fd = new FormData();
  fd.append('type', form.type);
  fd.append('prompt', form.prompt);
  fd.append('explanation', form.explanation);
  
  if (form.image_upload instanceof File) {
    fd.append('image_upload', form.image_upload);
  }

  if (form.type === 'multiple-choice') {
    const optionsPayload = options.value.map(opt => ({
      id: opt.id, // 'id' 可能是 undefined, 后端会处理
      text: opt.text,
      is_correct: opt.is_correct
    }));
    fd.append('options', JSON.stringify(optionsPayload));
    
  } else if (form.type === 'fill-in-the-blank') {
    const blanksPayload = blanks.value.map(blk => ({
      id: blk.id,
      index_number: blk.index_number,
      correct_answer: blk.correct_answer,
      case_sensitive: blk.case_sensitive
    }));
    fd.append('fill_in_blanks', JSON.stringify(blanksPayload));
  }

  try {
    if (isEditMode.value && props.exercise) {
      // 编辑模式
      await updateMyExercise(String(props.exercise.id), fd);
    } else {
      // 创建模式
      await createMyExercise(String(props.chapterId), fd);
    }
    emit('saved'); // 通知父组件 (ExerciseManager)
  } catch (err) {
    console.error("练习题保存失败:", err);
    if (isAxiosError(err) && err.response?.data) {
      // 后端现在可以返回清晰的 JSON 错误
      const errors = err.response.data;
      if (typeof errors === 'object') {
        error.value = `保存失败: ${Object.values(errors).flat().join(' ')}`;
      } else {
        error.value = `保存失败: ${JSON.stringify(errors)}`;
      }
    } else {
      error.value = "保存失败，请重试。";
    }
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.exercise-form { position: relative; }
.modal-close-btn { position: absolute; top: 10px; right: 15px; font-size: 1.5rem; background: none; border: none; cursor: pointer; }
.image-preview { max-width: 200px; height: auto; margin-top: 10px; }
.dynamic-form-section { border: 1px solid #eee; padding: 15px; margin-top: 15px; border-radius: 5px; }
.option-item, .blank-item { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; align-items: center; }
.blank-item input[type="number"] { width: 60px; }
.btn-submit { background-color: #4CAF50; color: white; margin-top: 15px; }
</style>