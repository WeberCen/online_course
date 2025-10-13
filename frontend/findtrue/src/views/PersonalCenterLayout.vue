<template>
  <div class="personal-center">
    <aside class="sidebar">
      <nav>
        <router-link :to="{ name: 'my-profile' }">我的资料</router-link>
        <router-link :to="{ name: 'my-collections' }">我的收藏</router-link>
        <router-link :to="{ name: 'my-creations' }">我的创作</router-link>
        <router-link :to="{ name: 'my-supported' }">我的已购</router-link>
        <router-link :to="{ name: 'my-participations' }">我的参与</router-link>
        <router-link :to="{ name: 'message-inbox' }">我的消息</router-link>
      </nav>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router';
</script>

<style scoped>
.personal-center {
  display: flex;
  gap: 2rem;
  max-width: 1200px;
  margin: 2rem auto;
}
.sidebar {
  flex: 0 0 200px;
  border-right: 1px solid #eee;
}
.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.sidebar nav a {
  text-decoration: none;
  color: #333;
  padding: 10px;
  border-radius: 4px;
}
.sidebar nav a.router-link-exact-active {
  background-color: #007bff;
  color: white;
}
.content {
  flex: 1;
}
</style>