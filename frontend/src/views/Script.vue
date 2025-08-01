<template>
  <div class="script-page">
    <el-card class="script-card" shadow="hover">
      <template #header>
        <span>脚本管理</span>
      </template>
      
      <div class="script-content">
        <el-alert
          title="脚本管理功能开发中..."
          type="info"
          :closable="false"
          show-icon
        >
          <p>脚本录制、编辑、回放等功能正在开发中</p>
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// 脚本管理页面
</script>

<style lang="scss" scoped>
.script-page {
  .script-card {
    .script-content {
      min-height: 400px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}
</style> 