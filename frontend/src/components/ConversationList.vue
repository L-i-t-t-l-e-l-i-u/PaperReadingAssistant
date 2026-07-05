<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { useConversationStore } from '@/store/conversation'

const convStore = useConversationStore()

const handleNewConversation = () => {
  convStore.startNewConversation()
}

const handleSwitchConversation = async (conversationId: number) => {
  if (convStore.currentConversationId === conversationId) return
  await convStore.switchConversation(conversationId)
}

const handleDeleteConversation = async (conversationId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个会话吗？所有聊天记录将被清除。',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await convStore.deleteConversation(conversationId)
    ElMessage.success('会话已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 格式化时间显示
const formatTime = (dateStr: string | null) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffHour < 24) return `${diffHour}小时前`
  if (diffDay < 7) return `${diffDay}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}
</script>

<template>
  <div class="conversation-sidebar">
    <div class="sidebar-top">
      <div class="sidebar-title">对话列表</div>
      <el-button
        type="primary"
        :icon="Plus"
        size="small"
        @click="handleNewConversation"
        class="new-chat-btn"
      >
        新对话
      </el-button>
    </div>

    <el-scrollbar class="conversation-list-scrollbar">
      <div class="conversation-list">
        <div
          v-for="conv in convStore.conversations"
          :key="conv.id"
          :class="['conversation-item', { active: conv.id === convStore.currentConversationId }]"
          @click="handleSwitchConversation(conv.id)"
        >
          <div class="conv-info">
            <el-icon class="conv-icon"><ChatDotRound /></el-icon>
            <span class="conv-title">{{ conv.title }}</span>
          </div>
          <div class="conv-meta">
            <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
            <el-button
              :icon="Delete"
              size="small"
              type="danger"
              text
              class="conv-delete-btn"
              @click.stop="handleDeleteConversation(conv.id)"
            />
          </div>
        </div>

        <div v-if="convStore.conversations.length === 0" class="empty-hint">
          还没有对话记录，开始新对话吧
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<style scoped>
.conversation-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-title {
  font-size: 15px;
  font-weight: bold;
  color: #303133;
}

.new-chat-btn {
  font-size: 13px;
}

.conversation-list-scrollbar {
  flex: 1;
  min-height: 0;
}

.conversation-list {
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #fff;
  border: 1px solid transparent;
}

.conversation-item:hover {
  background-color: #ecf5ff;
  border-color: #d9ecff;
}

.conversation-item.active {
  background-color: #e6f1fc;
  border-color: #409eff;
  color: #409eff;
}

.conv-info {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.conv-icon {
  margin-right: 8px;
  font-size: 16px;
  flex-shrink: 0;
}

.conv-title {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.conv-time {
  font-size: 11px;
  color: #909399;
}

.conv-delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .conv-delete-btn {
  opacity: 1;
}

.empty-hint {
  padding: 20px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}
</style>