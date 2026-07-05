<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChatWithLLMStream } from "@/request/api"
import { useConversationStore } from '@/store/conversation'

import ConversationList from './ConversationList.vue'
import ChatHistory from './ChatHistory.vue'
import ChatInput from './ChatInput.vue'
import ReferenceSidebar from './ReferenceSidebar.vue'
import PaperList from './PaperList.vue'

const convStore = useConversationStore()
const isStreaming = ref(false)
const paperListRef = ref<InstanceType<typeof PaperList> | null>(null)

// 计算属性：动态抓取最后一次 AI 回答里引用的文献
const currentSources = computed(() => {
  if (convStore.currentMessages.length === 0) return [];
  for (let i = convStore.currentMessages.length - 1; i >= 0; i--) {
    const msg = convStore.currentMessages[i];
    if (msg.role === 'assistant' && msg.sources && msg.sources.length > 0) {
      return msg.sources;
    }
  }
  return [];
});

// 页面加载时获取会话列表
onMounted(async () => {
  await convStore.loadConversations()
})

// 清空知识库成功后，刷新论文列表
const handleClearSuccess = () => {
  convStore.startNewConversation()
  paperListRef.value?.loadPapers()
}

// 核心流式通信骨架
const handleSendMessage = async (text: string) => {
  if (isStreaming.value) return  // 防止并发发送

  // 1. 本地先添加用户消息到列表
  convStore.addLocalMessage('user', text)

  // 2. 添加一条空的助手占位消息
  convStore.addLocalMessage('assistant', '', [])

  // 3. 构造请求参数，带上当前 conversation_id（可能为 null）
  const requestMessages = convStore.currentMessages.slice(0, -1).map(m => ({
    role: m.role,
    content: m.content,
  }))

  isStreaming.value = true

  try {
    const response = await ChatWithLLMStream({
      messages: requestMessages,
      conversation_id: convStore.currentConversationId,
    });

    const reader = response.body?.getReader();
    if (!reader) throw new Error('无法获取数据流阅读器');

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 正则拦截并剥除特殊标签（文献来源）
      const sourceRegex = /\[\[SOURCES:(.*?)\]\]/;
      const match = buffer.match(sourceRegex);

      if (match) {
        convStore.updateLastMessageSources(match[1].split(','))
        buffer = buffer.replace(match[0], '');
      }

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.trim() === '' || !line.startsWith('data: ')) continue;
        const dataStr = line.slice(6).trim();
        if (dataStr === '[DONE]') continue;

        try {
          const dataObj = JSON.parse(dataStr);

          // 处理 meta 事件（后端发送的会话 ID）
          if (dataObj.type === 'meta' && dataObj.conversation_id) {
            const newConvId = dataObj.conversation_id
            convStore.setConversationId(newConvId)
            // 在列表头部插入这个新会话
            const title = text.slice(0, 20).trim() || '新对话'
            convStore.prependConversation(newConvId, title)
            continue
          }

          const content = dataObj.choices?.[0]?.delta?.content || '';
          if (content) {
            convStore.updateLastMessageContent(content)
          }
        } catch (err) {
          console.warn('流解析异常', err);
        }
      }
    }

    // 流结束后的防御性检查：如果 meta 事件没被成功解析，从服务端拉取最新会话
    if (convStore.currentConversationId === null) {
      console.warn('meta 事件未被解析，从服务端刷新会话列表');
      await convStore.loadConversations();
      if (convStore.conversations.length > 0) {
        const latestConv = convStore.conversations[0];
        convStore.setConversationId(latestConv.id);
      }
    }

  } catch (error) {
    console.error('流请求崩溃:', error);
  } finally {
    isStreaming.value = false
  }
};
</script>

<template>
  <div class="chat-full-layout">
    <div class="left-sidebar">
      <ConversationList class="conv-sidebar" />
      <PaperList ref="paperListRef" />
    </div>

    <div class="chat-center">
      <div class="chat-wrapper">
        <ChatHistory :messages="convStore.currentMessages" />
        <ChatInput
          @send="handleSendMessage"
          @clear-success="handleClearSuccess"
          @upload-success="paperListRef?.loadPapers()"
          :disabled="isStreaming"
        />
      </div>
    </div>

    <ReferenceSidebar :sources="currentSources" />
  </div>
</template>

<style scoped>
.chat-full-layout {
  display: flex;
  height: 80vh;
  margin: 1vh 20px;
  gap: 10px;
  transition: all 0.3s ease;
}

.left-sidebar {
  display: flex;
  flex-direction: column;
  flex: 0 0 220px;
  min-width: 0;
  height: 100%;
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.conv-sidebar {
  flex: 1;
  min-height: 0;
}

.chat-center {
  flex: 1;
  min-width: 0;
  transition: all 0.3s ease;
}

.chat-wrapper {
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 15px;
  background-color: #f9fafc;
  height: 100%;
  box-sizing: border-box;
}
</style>