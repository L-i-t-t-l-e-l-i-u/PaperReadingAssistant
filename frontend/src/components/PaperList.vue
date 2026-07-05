<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder, Delete, Document } from '@element-plus/icons-vue'
import { GetPapers, DeletePaper } from '@/request/api'

interface PaperItem {
  id: number
  filename: string
  title: string
  chunks_count: number
  uploaded_at: string | null
}

const papers = ref<PaperItem[]>([])
const isLoading = ref(false)

const loadPapers = async () => {
  isLoading.value = true
  try {
    const result = await GetPapers()
    papers.value = result.papers
  } catch (error) {
    console.error('加载论文列表失败:', error)
  } finally {
    isLoading.value = false
  }
}

const displayName = (paper: PaperItem) => {
  return paper.title && paper.title.trim() ? paper.title : paper.filename
}

const handleDeletePaper = async (paper: PaperItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除论文《${displayName(paper)}》吗？该论文产生的所有知识块（${paper.chunks_count} 个）也将一并删除，此操作不可逆。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await DeletePaper(paper.id)
    ElMessage.success(`论文《${displayName(paper)}》已删除`)
    await loadPapers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  loadPapers()
})

// 暴露刷新方法给父组件
defineExpose({ loadPapers })
</script>

<template>
  <div class="paper-library">
    <div class="paper-header">
      <div class="header-title">
        <el-icon><Folder /></el-icon>
        <span>论文库</span>
        <el-tag size="small" type="info" class="count-tag">{{ papers.length }}</el-tag>
      </div>
    </div>

    <el-scrollbar class="paper-scrollbar">
      <div v-loading="isLoading" class="paper-list">
        <div
          v-for="paper in papers"
          :key="paper.id"
          class="paper-item"
        >
          <div class="paper-info">
            <el-icon class="paper-doc-icon"><Document /></el-icon>
            <div class="paper-detail">
              <span class="paper-title" :title="displayName(paper)">{{ displayName(paper) }}</span>
              <span v-if="paper.title && paper.title !== paper.filename" class="paper-filename" :title="paper.filename">{{ paper.filename }}</span>
              <div class="paper-meta">
                <span class="chunk-count">{{ paper.chunks_count }} 块</span>
                <span class="upload-time">{{ formatDate(paper.uploaded_at) }}</span>
              </div>
            </div>
          </div>
          <el-button
            :icon="Delete"
            size="small"
            type="danger"
            text
            class="paper-delete-btn"
            @click="handleDeletePaper(paper)"
          />
        </div>

        <div v-if="papers.length === 0 && !isLoading" class="empty-hint">
          还没有上传论文
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<style scoped>
.paper-library {
  display: flex;
  flex-direction: column;
  border-top: 1px solid #e4e7ed;
  background-color: #f5f7fa;
  max-height: 40%;
}

.paper-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 15px;
  border-bottom: 1px solid #e4e7ed;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: bold;
  color: #303133;
}

.count-tag {
  margin-left: 2px;
}

.paper-scrollbar {
  flex: 1;
  min-height: 0;
}

.paper-list {
  padding: 8px;
}

.paper-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  margin-bottom: 4px;
  border-radius: 6px;
  background-color: #fff;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.paper-item:hover {
  background-color: #fef0f0;
  border-color: #fde2e2;
}

.paper-info {
  display: flex;
  align-items: flex-start;
  flex: 1;
  min-width: 0;
  gap: 8px;
}

.paper-doc-icon {
  font-size: 18px;
  color: #e6a23c;
  flex-shrink: 0;
  margin-top: 2px;
}

.paper-detail {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.paper-title {
  font-size: 12px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.paper-filename {
  font-size: 11px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
  margin-top: 1px;
}

.paper-meta {
  display: flex;
  gap: 8px;
  margin-top: 3px;
}

.chunk-count {
  font-size: 11px;
  color: #409eff;
}

.upload-time {
  font-size: 11px;
  color: #909399;
}

.paper-delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.paper-item:hover .paper-delete-btn {
  opacity: 1;
}

.empty-hint {
  padding: 20px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}
</style>
