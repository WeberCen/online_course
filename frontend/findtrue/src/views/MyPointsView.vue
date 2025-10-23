<template>
  <div class="points-view">
    
    <div v-if="userStore.userInfo" class="points-summary-card">
      <h3>我的当前积分</h3>
      <div class="total-points-display">
        {{ userStore.userInfo.currentPoints }}
      </div>
    </div>
    <div v-else class="points-summary-card">
      <h3>我的当前积分</h3>
      <div class="total-points-display">...</div> </div>


    <div class="points-history-list">
      <h4>积分流水</h4>
      
      <div v-if="loading" class="loading-state">
        <p>正在加载流水记录...</p>
      </div>
      
      <div v-else-if="error" class="error-state">
        <p>加载失败: {{ error.message }}</p>
        <button @click="loadPage('/my/points/')">重试</button>
      </div>

      <div v-else-if="transactions.length === 0" class="empty-state">
        <p>您还没有任何积分记录。</p>
      </div>

      <table v-else>
        <thead>
          <tr>
            <th>时间</th>
            <th>类型</th>
            <th>详情</th>
            <th class="text-right">积分变动</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tx in transactions" :key="tx.id">
            <td class="time-cell">{{ formatDateTime(tx.created_at) }}</td>
            <td>{{ tx.transaction_type_display }}</td>
            <td>
              <router-link v-if="tx.related_link" :to="tx.related_link">
                {{ tx.description }}
              </router-link>
              <span v-else>{{ tx.description }}</span>
            </td>
            <td class="text-right">
              <span :class="tx.amount > 0 ? 'points-credit' : 'points-debit'">
                {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div class="pagination" v-if="pagination.next || pagination.previous">
        <button @click="loadPage(pagination.previous)" :disabled="!pagination.previous">
          &lt; 上一页
        </button>
        <button @click="loadPage(pagination.next)" :disabled="!pagination.next">
          下一页 &gt;
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getMyPointsHistory } from '@/services/apiService'; 
import type { PointsTransaction } from '@/types'; 
import { useUserStore } from '@/stores/userStore'; 

// --- 状态 ---
const userStore = useUserStore();

// 本地组件状态
const transactions = ref<PointsTransaction[]>([]);
const pagination = ref({
  count: 0,
  next: null as string | null,
  previous: null as string | null,
});
const loading = ref(true);
const error = ref<Error | null>(null);

// --- 方法 ---

/**
 * 加载特定页面的流水数据
 * @param url 完整的 API URL (由 onMounted 或分页按钮提供)
 */
async function loadPage(url: string | null) {
  // 如果 URL 为 null (例如在第一页点"上一页")，则不执行任何操作
  if (!url) return;

  loading.value = true;
  error.value = null;
  
  try {
    const data = await getMyPointsHistory(url); 
    transactions.value = data.results;
    pagination.value = {
      count: data.count,
      next: data.next,
      previous: data.previous
    };

  } catch (err) {
    if (err instanceof Error) {
      error.value = err;
    } else {
      error.value = new Error('加载积分历史时发生未知错误');
    }
  } finally {
    loading.value = false;
  }
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  // 你可以使用更专业的库 (Day.js, date-fns)，但这是原生JS的简单实现
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// --- 生命周期 ---
onMounted(() => {
  // Pinia store 可能已经在 PersonalCenterLayout 中加载了用户信息
  // 如果没有，你可以在这里触发一次:
  if (!userStore.userInfo) {
     // userStore.fetchUserInfo(); // 假设 store 有这个 action
     console.warn("MyPointsView: UserInfo 尚未加载，总积分可能无法显示。");
  }

  loadPage('/my/points/');
});
</script>

<style scoped>
.points-view {
  max-width: 900px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.points-summary-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.points-summary-card h3 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 1rem;
  font-weight: 500;
  color: #6c757d;
}

.total-points-display {
  font-size: 2.5rem;
  font-weight: 700;
  color: #212529;
}

.points-history-list h4 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 16px;
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 40px;
  color: #6c757d;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.error-state p {
  color: #dc3545;
}

.error-state button {
  padding: 8px 16px;
  font-weight: 600;
  border: 1px solid #007bff;
  background-color: #007bff;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px 10px;
  border-bottom: 1px solid #dee2e6;
  text-align: left;
  vertical-align: top;
}

th {
  font-weight: 600;
  color: #495057;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.time-cell {
  font-size: 0.9rem;
  color: #6c757d;
  white-space: nowrap;
}

.text-right {
  text-align: right;
}

/* 关键样式: 收入/支出 */
.points-credit {
  color: #28a745; /* 绿色 */
  font-weight: 600;
  font-feature-settings: "tnum"; /* 等宽数字 */
}

.points-debit {
  color: #dc3545; /* 红色 */
  font-weight: 600;
  font-feature-settings: "tnum";
}

a {
  color: #007bff;
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination button {
  padding: 8px 16px;
  font-weight: 600;
  border: 1px solid #dee2e6;
  background-color: #fff;
  color: #007bff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.pagination button:hover:not(:disabled) {
  background-color: #007bff;
  color: #fff;
}
.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
  color: #6c757d;
}
</style>