import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { useUserStore } from './stores/userStore';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

// 初始化用户状态
const userStore = useUserStore(pinia);
userStore.initializeUser();

app.mount('#app');