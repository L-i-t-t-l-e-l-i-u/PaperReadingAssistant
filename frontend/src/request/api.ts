import instance from "@/request/http";
import loginInstance from "@/request/http_login"

//一般情况下，接口类型会放到一个文件
// 下面两个TS接口，表示要传的参数
interface ReqLogin {
    username: string
    password: string
}
interface ResLogin {
    access_token: string
}

interface ReqRegister {
    username: string
    email: string
    first_name: string
    last_name: string
    password: string
}


// Res是返回的参数，T是泛型，需要自己定义，返回对数统一管理***
type Res<T> = Promise<ItypeAPI<T>>;
// 一般情况下响应数据返回的这三个参数，
// 但不排除后端返回其它的可能性，
interface ItypeAPI<T> {
    success: string | null // 返回状态码的信息，如请求成功等;
    result: T,//请求的数据，用泛型
    msg: string | null // 返回状态码的信息，如请求成功等
    message:string
    code: number //返回后端自定义的200，404，500这种状态码
    user: User
    users: User[]
    total_users: number
    total_pages: number
}

interface User {
    username: string
    email: string
    first_name: string
    last_name: string
    is_active: boolean
    is_superuser: boolean
}

interface UserList {
    total: number
    users: User[]
}

interface Message {
    role: 'user' | 'assistant' | 'system' | string;
    content: string;
}



interface LLMRequest {
    messages: Message[];
    conversation_id?: number | null;
}

interface LLMResponse {
    response: string
}

// ---- 会话管理接口类型 ----

interface ConversationItem {
    id: number
    title: string
    created_at: string | null
    updated_at: string | null
    message_count: number
}

interface ConversationListResult {
    total: number
    conversations: ConversationItem[]
}

interface MessageItem {
    id: number
    role: string
    content: string
    created_at: string | null
}

interface ConversationDetail {
    id: number
    title: string
    created_at: string | null
    updated_at: string | null
    messages: MessageItem[]
}

interface MessageCreateData {
    role: string
    content: string
}


//测试hello api
export const TestHello = (): Res<null> =>
    instance.get('/api/hello');

//登录 api
export const LoginApi = (data: ReqLogin): Promise<ResLogin> =>
    loginInstance.post('/api/token', data);

//注册 api
export const RegisterApi = (data: ReqRegister): Promise<User> =>
    instance.post('/api/users/', data);

//登出 api
export const LogoutApi = (): Res<null> =>
    instance.get('/api/logout');

//根据username查询用户信息api  get
export const GetUserInfoByUserName = (params: { userName: string }): Promise<User> =>
    instance.get(`/api/users/name/${params.userName}`);

export const GetUserInfoList = (params: { skip: number, limit: number }): Promise<UserList> =>
    instance.get(`/api/users/`, {params});

export const ChatWithLLM = (data: LLMRequest): Promise<LLMResponse> =>
    instance.post(`/api/chat`, data);

// 新的、用于流式响应的函数
export const ChatWithLLMStream = async (data: LLMRequest): Promise<Response> => {
  // 使用 fetch API，因为它能更原生地支持流式响应
    const token = localStorage.getItem('access_token') || '';
  const response = await fetch('/api/chat/stream', { // 注意：这里的端点可能是 /api/chat/stream
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // 如果需要认证，可以在这里添加，例如：
        'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data)
  });

  // 401 鉴权失败：清除登录态，跳转登录页
  if (response.status === 401) {
    const { useUserstore } = await import('@/store/user')
    const userStore = useUserstore()
    userStore.logout()
    throw new Error('登录已过期，请重新登录')
  }

  return response;
  // 注意：这个函数返回的是原始的 Response 对象，其 body 是一个 ReadableStream
  // 具体的流读取和解析逻辑将在调用它的组件（如 Chat.vue）中完成
};


// 1. 定义后端返回的数据结构接口（保持你代码严格的 TS 规范）
interface ResUpload {
    message: string;
    filename: string;
    chunks_count: number;
}

// 2. 新增：文档上传 API
export const UploadKnowledgeDocument = (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);

    // 重点：不要写 headers！让浏览器和 axios 自动处理 FormData
    return instance.post('/api/upload', formData);
};


export const ClearKnowledgeDatabase = () => {
    // 使用你顶部引入的 instance，并且按照 axios 的标准用法
    return instance.delete('/api/clear');
}


// ---- 会话管理 API ----

// 获取当前用户的会话列表
export const GetConversations = (params: { skip: number, limit: number }): Promise<ConversationListResult> =>
    instance.get('/api/conversations/', { params });

// 获取某个会话的详情（包含所有消息）
export const GetConversationDetail = (conversationId: number): Promise<ConversationDetail> =>
    instance.get(`/api/conversations/${conversationId}`);

// 删除某个会话
export const DeleteConversation = (conversationId: number): Promise<any> =>
    instance.delete(`/api/conversations/${conversationId}`);

// 保存一条消息到某个会话（前端在流式完成后调用）
export const SaveMessage = (conversationId: number, data: MessageCreateData): Promise<MessageItem> =>
    instance.post(`/api/conversations/${conversationId}/messages`, data);


// ---- 论文管理 API ----

interface PaperItem {
    id: number
    filename: string
    title: string
    chunks_count: number
    uploaded_at: string | null
}

interface PaperListResult {
    total: number
    papers: PaperItem[]
}

// 获取所有已上传的论文列表
export const GetPapers = (): Promise<PaperListResult> =>
    instance.get('/api/papers/');

// 删除指定论文及其所有知识块
export const DeletePaper = (paperId: number): Promise<any> =>
    instance.delete(`/api/papers/${paperId}`);