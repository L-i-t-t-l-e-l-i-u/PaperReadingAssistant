import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  GetConversations,
  GetConversationDetail,
  DeleteConversation,
} from '@/request/api'

interface ConversationItem {
  id: number
  title: string
  created_at: string | null
  updated_at: string | null
  message_count: number
}

interface MessageItem {
  id: number
  role: string
  content: string
  created_at: string | null
  sources?: string[]
}

export const useConversationStore = defineStore('conversation', () => {
  // 会话列表
  const conversations = ref<ConversationItem[]>([])
  const totalConversations = ref(0)

  // 当前活跃会话
  const currentConversationId = ref<number | null>(null)
  const currentMessages = ref<MessageItem[]>([])

  // 加载状态
  const isLoadingConversations = ref(false)
  const isLoadingMessages = ref(false)

  // 加载会话列表（从服务端刷新）
  const loadConversations = async (skip = 0, limit = 50) => {
    isLoadingConversations.value = true
    try {
      const result = await GetConversations({ skip, limit })
      conversations.value = result.conversations
      totalConversations.value = result.total
    } catch (error) {
      console.error('加载会话列表失败:', error)
    } finally {
      isLoadingConversations.value = false
    }
  }

  // 切换到某个会话（加载其消息历史）
  const switchConversation = async (conversationId: number) => {
    if (currentConversationId.value === conversationId) return
    isLoadingMessages.value = true
    currentConversationId.value = conversationId
    try {
      const detail = await GetConversationDetail(conversationId)
      currentMessages.value = detail.messages.map(m => ({
        ...m,
        sources: [] as string[],
      }))
    } catch (error) {
      console.error('加载会话消息失败:', error)
      currentMessages.value = []
    } finally {
      isLoadingMessages.value = false
    }
  }

  // 开始新对话（清空当前状态，等首次发消息时由后端自动创建）
  const startNewConversation = () => {
    currentConversationId.value = null
    currentMessages.value = []
  }

  // 后端自动创建会话后，前端收到 conversation_id 时更新状态
  const setConversationId = (id: number) => {
    currentConversationId.value = id
  }

  // 添加一条消息到当前本地消息列表（流式过程中用）
  const addLocalMessage = (role: string, content: string, sources?: string[]) => {
    currentMessages.value.push({
      id: 0, // 临时 id，后端保存后会分配真实 id
      role,
      content,
      created_at: null,
      sources: sources || [],
    })
  }

  // 更新最后一条消息的内容（流式追加时用）
  const updateLastMessageContent = (content: string) => {
    const lastIdx = currentMessages.value.length - 1
    if (lastIdx >= 0) {
      currentMessages.value[lastIdx].content += content
    }
  }

  // 更新最后一条消息的 sources
  const updateLastMessageSources = (sources: string[]) => {
    const lastIdx = currentMessages.value.length - 1
    if (lastIdx >= 0) {
      currentMessages.value[lastIdx].sources = sources
    }
  }

  // 删除某个会话（删除后从服务端重新拉取列表，确保一致性）
  const deleteConversation = async (conversationId: number) => {
    try {
      await DeleteConversation(conversationId)
      // 如果删除的是当前会话，清空消息
      if (currentConversationId.value === conversationId) {
        currentConversationId.value = null
        currentMessages.value = []
      }
      // 从服务端重新拉取完整列表，确保状态一致
      await loadConversations()
    } catch (error) {
      console.error('删除会话失败:', error)
      throw error
    }
  }

  // 在会话列表头部插入新创建的会话（后端返回 id 后）
  // 会检查是否已存在，避免重复
  const prependConversation = (id: number, title: string) => {
    const exists = conversations.value.some(c => c.id === id)
    if (exists) return
    conversations.value.unshift({
      id,
      title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      message_count: 1,
    })
    totalConversations.value += 1
  }

  return {
    conversations,
    totalConversations,
    currentConversationId,
    currentMessages,
    isLoadingConversations,
    isLoadingMessages,
    loadConversations,
    switchConversation,
    startNewConversation,
    setConversationId,
    addLocalMessage,
    updateLastMessageContent,
    updateLastMessageSources,
    deleteConversation,
    prependConversation,
  }
})