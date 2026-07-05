<script setup lang="ts">
import {ElMessage} from 'element-plus'
import {useUserstore} from "@/store/user";
const userStore = useUserstore()
async function logout() {
  userStore.logout()
  ElMessage.success("登出成功")
}
</script>

<template>
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" alt="Logo" style="height: 50px;">
    <div>
      <el-button type="info" @click="logout">登出</el-button>
    </div>
  </div>
</template>

<style scoped>

</style>