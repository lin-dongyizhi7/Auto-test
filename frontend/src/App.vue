<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-left">
          <h2 class="app-title">
            <el-icon><Monitor /></el-icon>
            QGIS自动化测试系统
          </h2>
        </div>
        <div class="header-right">
          <el-button-group>
            <el-button 
              :type="isConnected ? 'success' : 'danger'" 
              :icon="isConnected ? 'Connection' : 'Close'"
              size="small"
            >
              {{ isConnected ? '已连接' : '未连接' }}
            </el-button>
          </el-button-group>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-container class="main-container">
        <!-- 侧边栏 -->
        <el-aside width="200px" class="app-sidebar">
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            router
          >
            <el-menu-item index="/dashboard">
              <el-icon><DataBoard /></el-icon>
              <span>仪表板</span>
            </el-menu-item>
            <el-menu-item index="/operation">
              <el-icon><Operation /></el-icon>
              <span>操作控制</span>
            </el-menu-item>
            <el-menu-item index="/monitor">
              <el-icon><View /></el-icon>
              <span>实时监控</span>
            </el-menu-item>
            <el-menu-item index="/script">
              <el-icon><Document /></el-icon>
              <span>脚本管理</span>
            </el-menu-item>
            <el-menu-item index="/settings">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 主内容区 -->
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useOperationStore } from '@/stores/operation'

const route = useRoute()
const operationStore = useOperationStore()

const activeMenu = computed(() => route.path)
const isConnected = computed(() => operationStore.isConnected)
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  .header-left {
    .app-title {
      margin: 0;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .header-right {
    .el-button-group {
      .el-button {
        border: none;
        background: rgba(255, 255, 255, 0.2);
        color: white;
        
        &:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      }
    }
  }
}

.main-container {
  height: calc(100vh - 60px);
}

.app-sidebar {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;

  .sidebar-menu {
    border: none;
    background: transparent;
  }
}

.app-main {
  background: #ffffff;
  padding: 20px;
  overflow-y: auto;
}
</style> 