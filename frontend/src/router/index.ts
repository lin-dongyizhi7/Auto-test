import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表板' }
  },
  {
    path: '/operation',
    name: 'Operation',
    component: () => import('@/views/Operation.vue'),
    meta: { title: '操作控制' }
  },
  {
    path: '/monitor',
    name: 'Monitor',
    component: () => import('@/views/Monitor.vue'),
    meta: { title: '实时监控' }
  },
  {
    path: '/script',
    name: 'Script',
    component: () => import('@/views/Script.vue'),
    meta: { title: '脚本管理' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  },
  {
    path: '/machine/:id',
    name: 'MachineControl',
    component: () => import('@/views/MachineControl.vue'),
    meta: { title: '机器控制' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 