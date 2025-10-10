<template>
  <header>
    <nav>
      <router-link to="/courses">课程</router-link>
      <router-link to="/gallery">画廊</router-link>
      <router-link to="/communities">社群</router-link> 
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
header { padding: 1rem; border-bottom: 1px solid #ddd; }
nav a { margin-right: 1rem; }
main { padding: 1rem; }
</style>
