import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '首页' }
        },
        // 数据管理
        {
          path: 'teachers',
          name: 'Teachers',
          component: () => import('@/views/data/Teachers.vue'),
          meta: { title: '教师管理' }
        },
        {
          path: 'courses',
          name: 'Courses',
          component: () => import('@/views/data/Courses.vue'),
          meta: { title: '课程管理' }
        },
        {
          path: 'classes',
          name: 'Classes',
          component: () => import('@/views/data/Classes.vue'),
          meta: { title: '班级管理' }
        },
        {
          path: 'classrooms',
          name: 'Classrooms',
          component: () => import('@/views/data/Classrooms.vue'),
          meta: { title: '教室管理' }
        },
        {
          path: 'offerings',
          name: 'Offerings',
          component: () => import('@/views/data/Offerings.vue'),
          meta: { title: '开课计划' }
        },
        {
          path: 'preferences',
          name: 'Preferences',
          component: () => import('@/views/data/Preferences.vue'),
          meta: { title: '教师偏好' }
        },
        // 排课
        {
          path: 'scheduling',
          name: 'Scheduling',
          component: () => import('@/views/scheduling/Scheduling.vue'),
          meta: { title: '排课控制台' }
        },
        // 课表查询
        {
          path: 'timetable/teacher',
          name: 'TimetableTeacher',
          component: () => import('@/views/timetable/TeacherTimetable.vue'),
          meta: { title: '教师课表' }
        },
        {
          path: 'timetable/class',
          name: 'TimetableClass',
          component: () => import('@/views/timetable/ClassTimetable.vue'),
          meta: { title: '班级课表' }
        },
        {
          path: 'timetable/classroom',
          name: 'TimetableClassroom',
          component: () => import('@/views/timetable/ClassroomTimetable.vue'),
          meta: { title: '教室课表' }
        },
        {
          path: 'timetable/week',
          name: 'TimetableWeek',
          component: () => import('@/views/timetable/WeekTimetable.vue'),
          meta: { title: '周课表' }
        }
      ]
    }
  ]
})

export default router

