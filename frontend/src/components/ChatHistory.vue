<script setup lang="ts">
import { Document } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
// 🚨 关键改变：引入现代化的分支包
import markdownItKatex from '@iktakahiro/markdown-it-katex'
import 'katex/dist/katex.min.css'

interface Message {
  role: string;
  content: string;
  sources?: string[];
}

defineProps<{
  messages: Message[]
}>()

// 保留必要的 LLM 语法容错
const formatMath = (text: string) => {
  if (!text) return '';
  return text
    .replace(/(_|\^)\\text{([^}]+)}/g, '$1{\\text{$2}}')
    .replace(/\\\[/g, '$$$$')
    .replace(/\\\]/g, '$$$$')
    .replace(/\\\(/g, '$')
    .replace(/\\\)/g, '$')
    .replace(/(?<!\$)\$([^$]+?)\$(?!\$)/g, (match, p1) => `$${p1.trim()}$`);
}

const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true
}).use(markdownItKatex, {
  throwOnError: false,
  errorColor: '#cc0000'
})
</script>

<template>
  <div class="chat-history-container">
    <el-scrollbar class="chat-history-scrollbar">
      <div class="chat-inner-padding">

        <div v-for="(msg, index) in messages" :key="index" :class="['chat-bubble', msg.role]">
          <div class="role-name">{{ msg.role === 'user' ? '🧑‍💻 你' : '🤖 AI助手' }}</div>
          <div class="content markdown-body" v-html="md.render(formatMath(msg.content))"></div>
          <div v-if="msg.role === 'assistant' && msg.sources && msg.sources.length > 0" class="mini-source-hint">
            <el-icon style="vertical-align: middle;"><Document /></el-icon>
            已根据右侧 {{ msg.sources.length }} 篇文献生成回答
          </div>
        </div>

      </div>
    </el-scrollbar>
  </div>
</template>

<style scoped>
/* ========== 基础容器样式 ========== */
.chat-history-container {
  flex: 1;
  min-height: 0;
  background-color: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 20px;
  overflow: hidden;
}

.chat-history-scrollbar { height: 100%; }
.chat-inner-padding { padding: 15px; }

.chat-bubble {
  margin-bottom: 20px;
  padding: 10px 15px;
  border-radius: 8px;
  max-width: 80%;
}
.chat-bubble.user { background-color: #e1f3d8; margin-left: auto; }
.chat-bubble.assistant { background-color: #f4f4f5; margin-right: auto; }
.chat-bubble:last-child { margin-bottom: 0; }

.role-name {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.content {
  margin: 0;
  white-space: normal;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
}

.mini-source-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #dcdfe6;
}

/* ========== Markdown 基础排版 ========== */
:deep(.markdown-body table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
  background-color: #fff;
}
:deep(.markdown-body th), :deep(.markdown-body td) {
  border: 1px solid #dcdfe6;
  padding: 8px 12px;
  text-align: left;
}
:deep(.markdown-body th) { background-color: #f2f6fc; font-weight: bold; }
:deep(.markdown-body p) { margin-top: 0; margin-bottom: 10px; }

/* 列表紧凑化排版 */
:deep(.markdown-body ul), :deep(.markdown-body ol) {
  padding-left: 1.5em;
  margin-top: 0;
  margin-bottom: 10px;
}
:deep(.markdown-body li) { margin-bottom: 4px; }
:deep(.markdown-body li > p) { margin: 0; display: inline-block; }

/* * 🚨 删除了所有针对 .katex .vlist 的黑科技修复代码
 * 因为包更新后，结构和样式终于匹配了！我们只需要放大一点字号即可。
 */
:deep(.katex) {
  font-size: 1.05em;
  text-align: left;
}
:deep(.katex-display) {
  margin: 1em 0;
  display: block;
  text-align: center;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 5px 0;
}
</style>