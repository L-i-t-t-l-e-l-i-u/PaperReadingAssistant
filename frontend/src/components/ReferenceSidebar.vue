<script setup lang="ts">
import { ref } from 'vue'
import { Document, ArrowRight, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

defineProps<{
  sources: string[]
}>()

const isExpanded = ref(false)

const handlePaperClick = (filename: string) => {
  ElMessage.success(`正在打开文献：《${filename}》`);
  const fileUrl = `http://127.0.0.1:8001/files/${filename}`;
  window.open(fileUrl, '_blank');
}
</script>

<template>
  <div class="reference-wrapper">
    <!-- 折叠状态：显示一个窄条，带展开按钮 -->
    <div v-if="!isExpanded" class="reference-collapsed" @click="isExpanded = true" v-show="sources.length > 0">
      <el-icon><ArrowLeft /></el-icon>
      <div class="collapsed-label">
        <el-icon><Document /></el-icon>
        <span>{{ sources.length }}</span>
      </div>
    </div>

    <!-- 展开状态：显示完整列表 -->
    <div v-else class="reference-expanded">
      <div class="ref-header">
        <span>引用文献 ({{ sources.length }})</span>
        <el-icon class="collapse-btn" @click="isExpanded = false"><ArrowRight /></el-icon>
      </div>
      <el-scrollbar class="ref-scrollbar">
        <div
          v-for="(source, index) in sources"
          :key="index"
          class="ref-paper-item"
          @click="handlePaperClick(source)"
        >
          <el-icon class="paper-icon"><Document /></el-icon>
          <span class="paper-name">{{ source }}</span>
        </div>
      </el-scrollbar>
    </div>
  </div>
</template>

<style scoped>
.reference-wrapper {
  flex-shrink: 0;
  display: flex;
  height: 100%;
}

/* 折叠状态 */
.reference-collapsed {
  width: 36px;
  background-color: #f0f2f5;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.reference-collapsed:hover {
  background-color: #e6f0ff;
}

.collapsed-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 8px;
  font-size: 11px;
  color: #409eff;
  gap: 2px;
}

/* 展开状态 */
.reference-expanded {
  width: 180px;
  background-color: #f9fafc;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(10px); }
  to { opacity: 1; transform: translateX(0); }
}

.ref-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.collapse-btn {
  cursor: pointer;
  color: #909399;
  transition: color 0.2s;
}

.collapse-btn:hover {
  color: #409eff;
}

.ref-scrollbar {
  flex: 1;
  min-height: 0;
}

.ref-paper-item {
  display: flex;
  align-items: center;
  padding: 8px;
  margin-bottom: 8px;
  background-color: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ref-paper-item:hover {
  background-color: #ecf5ff;
  border-color: #b3d8ff;
}

.paper-icon {
  font-size: 16px;
  color: #409eff;
  margin-right: 6px;
  flex-shrink: 0;
}

.paper-name {
  font-size: 12px;
  color: #606266;
  word-break: break-all;
  line-height: 1.3;
}
</style>