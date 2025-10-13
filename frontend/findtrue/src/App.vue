<template>
  <header>
    <nav>
      <router-link to="/courses">课程</router-link>
      <router-link to="/gallery">画廊</router-link>
      <router-link to="/communities">社群</router-link>
       <router-link :to="{ name: 'my-collections' }">个人中心</router-link>
    </nav>
  </header>
  
  <main>
    <RouterView />
  </main>
</template>

<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
</script>

<style scoped>
.main-header {
  padding: 1rem 2rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: #ffffff;
}

.main-nav {
  display: flex;
  gap: 1.5rem;
}

.main-nav a {
  text-decoration: none;
  color: #333;
  font-weight: 500;
  padding: 0.5rem 0;
  position: relative;
  transition: color 0.3s;
}

.main-nav a:hover {
  color: #007bff;
}

.main-nav a.router-link-exact-active {
  color: #007bff;
  border-bottom: 2px solid #007bff;
}

.main-content {
  padding: 2rem;
}
</style>