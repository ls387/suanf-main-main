<template>
  <el-container class="main-layout">
    <el-aside width="200px">
      <div class="logo">
        <h2>智能排课系统</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="el-menu-vertical"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        
        <el-sub-menu index="data">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>数据管理</span>
          </template>
          <el-menu-item index="/teachers">教师管理</el-menu-item>
          <el-menu-item index="/courses">课程管理</el-menu-item>
          <el-menu-item index="/classes">班级管理</el-menu-item>
          <el-menu-item index="/classrooms">教室管理</el-menu-item>
          <el-menu-item index="/offerings">开课计划</el-menu-item>
          <el-menu-item index="/preferences">教师偏好</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/scheduling">
          <el-icon><Setting /></el-icon>
          <span>排课控制台</span>
        </el-menu-item>
        
        <el-sub-menu index="timetable">
          <template #title>
            <el-icon><Calendar /></el-icon>
            <span>课表查询</span>
          </template>
          <el-menu-item index="/timetable/teacher">教师课表</el-menu-item>
          <el-menu-item index="/timetable/class">班级课表</el-menu-item>
          <el-menu-item index="/timetable/classroom">教室课表</el-menu-item>
          <el-menu-item index="/timetable/week">周课表</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-content">
          <h3>{{ currentTitle }}</h3>
        </div>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '首页')
</script>

<style scoped>
.main-layout {
  height: 100%;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b3a4a;
}

.logo h2 {
  font-size: 18px;
  color: #fff;
  margin: 0;
}

.el-menu {
  border-right: none;
  background-color: #304156;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: #bfcbd9;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: #263445 !important;
  color: #fff;
}

:deep(.el-menu-item.is-active) {
  background-color: #409eff !important;
  color: #fff;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>

