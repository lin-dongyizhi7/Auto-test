<template>
  <div class="monitor-page">
    <el-card class="monitor-card" shadow="hover">
      <template #header>
        <span>实时监控</span>
      </template>
      
      <div class="monitor-content">
        <el-alert
          title="监控功能开发中..."
          type="info"
          :closable="false"
          show-icon
        >
          <p>实时截图、元素定位、操作日志等功能正在开发中</p>
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useOperationStore } from '@/stores/operation'

const operationStore = useOperationStore()
</script>

<style lang="scss" scoped>
.monitor-page {
  .monitor-card {
    .monitor-content {
      min-height: 400px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}
</style> 