import axios from 'axios'
import {useUserstore} from '@/store/user'

// 创建axios实例
const request = axios.create({
    baseURL: '',// 所有的请求地址前缀部分
    timeout: 80000, // 请求超时时间(毫秒)
    withCredentials: true,// 异步请求携带cookie
    headers: {
        'Content-Type': 'application/json',
    }
})
request.defaults.withCredentials = true;
// request拦截器
request.interceptors.request.use(
    config => { // 习惯上这里参数叫 config 会更清晰，其实叫 request 也行
        const userStore = useUserstore()
        if (userStore.token) {
            config.headers.Authorization = `Bearer ${userStore.token}`
        }

        // ==========================================
        // 【核心修复】：如果是上传文件 (FormData)，必须删掉原有的 JSON 请求头
        // 这样浏览器才会自动补全正确的 multipart/form-data; boundary=...
        // ==========================================
        if (config.data instanceof FormData) {
            delete config.headers['Content-Type'];
        }

        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// response 拦截器
request.interceptors.response.use(
    response => {
        // 对响应数据做点什么
        return response.data
    },
    error => {
        // 401 鉴权失败：清除登录态，跳转登录页
        if (error.response && error.response.status === 401) {
            const userStore = useUserstore()
            userStore.logout()
        }
        return Promise.reject(error)
    }
)
export default request