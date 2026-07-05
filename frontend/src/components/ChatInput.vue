<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadKnowledgeDocument, ClearKnowledgeDatabase } from "@/request/api";

// 定义向外通知父 components 的事件
const emit = defineEmits<{
  (e: 'send', text: string): void
  (e: 'clear-success'): void
  (e: 'upload-success'): void
}>()

// 接收父组件传入的禁用状态（流式发送期间不可再次发送）
defineProps<{
  disabled?: boolean
}>()

const currentInput = ref('')
const isUploading = ref(false)
const isClearing = ref(false)

// 触发发送
const handleSend = () => {
  const trimmed = currentInput.value.trim()
  if (!trimmed) return
  emit('send', trimmed)
  currentInput.value = '' // 清空输入框
}

// 处理文档上传
const customUpload = async (options: any) => {
  const file = options.file;
  const isValidFormat = file.name.endsWith('.pdf') || file.name.endsWith('.docx');
  if (!isValidFormat) {
    ElMessage.error('只能上传 .pdf 或 .docx 格式的文档！');
    return;
  }

  isUploading.value = true;
  try {
    const response: any = await UploadKnowledgeDocument(file);
    const filename = response.filename || response.data?.filename || file.name;
    const chunksCount = response.chunks_count || response.data?.chunks_count || 0;
    ElMessage.success(`《${filename}》解析入库成功！共生成 ${chunksCount} 个知识块。`);
    emit('upload-success');
  } catch (error: any) {
    console.error('上传失败:', error);
    const errorMsg = error.response?.data?.detail || error.message || '文档解析入库失败，请稍后重试';
    ElMessage.error(errorMsg);
  } finally {
    isUploading.value = false;
  }
};

// 一键清空微服务接口
const clearDatabase = async () => {
  try {
    await ElMessageBox.confirm(
      '这将永久删除知识库中的所有向量数据，并销毁已上传的所有物理文件。此操作不可逆，确定要清空吗？',
      '危险操作',
      { confirmButtonText: '确定清空', cancelButtonText: '取消', type: 'warning' }
    );

    isClearing.value = true;
    await ClearKnowledgeDatabase();
    ElMessage.success('知识库和物理文件已全部被清空！');
    emit('clear-success')

  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('清理失败，请检查后端运行状态');
      console.error(error);
    }
  } finally {
    isClearing.value = false;
  }
}
</script>

<template>
  <div class="input-area">
    <el-upload
      class="upload-demo"
      action="#"
      :http-request="customUpload"
      :show-file-list="false"
      accept=".pdf,.docx"
      :disabled="isUploading || isClearing"
    >
      <el-button type="primary" plain class="upload-btn" :loading="isUploading">
        <div style="line-height: 1.5;">{{ isUploading ? '正在入库...' : '上传\n文档' }}</div>
      </el-button>
    </el-upload>

    <el-button
      type="danger"
      plain
      class="clear-btn"
      :loading="isClearing"
      :disabled="isUploading"
      @click="clearDatabase"
    >
      <div style="line-height: 1.5;">{{ isClearing ? '清理中' : '清空\n知识' }}</div>
    </el-button>

    <el-input
      v-model="currentInput"
      type="textarea"
      :rows="3"
      placeholder="输入关于论文的问题..."
      @keyup.enter="handleSend"
      :disabled="disabled"
    />

    <el-button type="success" class="send-btn" @click="handleSend" :disabled="disabled">
      发送
    </el-button>
  </div>
</template>

<style scoped>
.input-area {
  display: flex;
  gap: 15px;
  align-items: flex-end;
  /* 👇 加上这一句，拒绝被压缩（0 表示不收缩） */
  flex-shrink: 0;
}
.upload-demo {
  flex-shrink: 0;
}
.upload-btn, .clear-btn {
  height: 75px;
  width: 80px;
  padding: 0;
  white-space: pre-wrap;
  flex-shrink: 0;
}
.send-btn {
  height: 75px;
  width: 80px;
  flex-shrink: 0;
}
</style>