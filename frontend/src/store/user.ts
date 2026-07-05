import {defineStore} from "pinia";

export const useUserstore = defineStore(
    'user',
    {
        state() {
            return {
                userName: localStorage.getItem('userName') || '',
                token: localStorage.getItem('access_token') || '',
            }
        },
        getters: {
            isAuthenticated: (state) => !!state.token,
        },
        actions: {
            setAuth(token: string, userName: string) {
                this.token = token
                this.userName = userName
                localStorage.setItem('access_token', token)
                localStorage.setItem('userName', userName)
            },
            logout() {
                this.token = ''
                this.userName = ''
                localStorage.removeItem('access_token')
                localStorage.removeItem('userName')
                // 延迟导入 router，避免循环依赖
                import('@/router').then(({ default: router }) => {
                    router.push({ name: 'Login' })
                })
            },
        }
    }
)