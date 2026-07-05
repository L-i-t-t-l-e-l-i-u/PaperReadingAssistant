import {createRouter, createWebHistory} from "vue-router";

import Login from '@/pages/Login.vue';
import Index from "@/pages/Index.vue";
import Test from "@/pages/Test.vue";
import CheckUserInfo from "@/components/CheckUserInfo.vue";
import Profile from "@/components/Profile.vue";
import AddUser from "@/components/AddUser.vue";
import Chat from "@/components/Chat.vue";
import Register from "@/pages/Register.vue";
import {useUserstore} from "@/store/user";

const routes =
    [
        {
            path: '/',
            name: 'Login',
            component: Login,
            meta: { guestOnly: true }
        },
        {
            path: '/register',
            name: 'Register',
            component: Register,
            meta: { guestOnly: true }
        },
        {
            path: '/index',
            name: 'Index',
            component: Index,
            meta: { requiresAuth: true },
            children: [
                {
                    path: '',
                    name:'IndexMain',
                    component: Profile,
                },
                {
                    path: 'checkUserInfo/:username',
                    name: 'checkUserDetail',
                    component: Profile,
                    props: true
                },
                {
                    path: 'checkUserInfo',
                    component: CheckUserInfo,
                },
                {
                    path: 'addUser',
                    component: AddUser,
                },
                {
                    path: 'chat',
                    component: Chat,
                },
            ]

        },
        {
            path: '/test',
            name: 'Test',
            component: Test
        }
    ];

const router = createRouter({
    history: createWebHistory(),
    routes
});

// 全局路由守卫：未登录用户访问需要鉴权的页面时，强制跳转登录页
// 已登录用户访问登录/注册页时，跳转到主页
router.beforeEach((to, _from, next) => {
    const userStore = useUserstore()

    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!userStore.isAuthenticated) {
            next({ name: 'Login' })
            return
        }
    }

    if (to.matched.some(record => record.meta.guestOnly)) {
        if (userStore.isAuthenticated) {
            next({ name: 'Index' })
            return
        }
    }

    next()
})

export default router;
