import { defineStore } from 'pinia';
import type { User } from '../types';

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null as User | null,
    isLoggedIn: false
  }),
  
  actions: {
    // 初始化用户状态
    initializeUser() {
      const userInfo = localStorage.getItem('userInfo');
      const accessToken = localStorage.getItem('accessToken');
      
      if (userInfo && accessToken) {
        this.userInfo = JSON.parse(userInfo);
        this.isLoggedIn = true;
      } else {
        this.clearUser();
      }
    },
    
    // 设置用户信息
    setUser(userInfo: User) {
      this.userInfo = userInfo;
      this.isLoggedIn = true;
      localStorage.setItem('userInfo', JSON.stringify(userInfo));
    },
    
    // 清除用户信息
    clearUser() {
      this.userInfo = null;
      this.isLoggedIn = false;
      localStorage.removeItem('userInfo');
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }
});