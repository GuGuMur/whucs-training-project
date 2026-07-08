<script setup lang="ts">
import { computed, reactive, shallowRef } from 'vue'
import { LogIn } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = reactive({
  account: 'xiaoming',
  email: 'xiaoming@example.com',
  password: 'Str0ngPass!',
  username: 'xiaoming',
})
const mode = shallowRef<'login' | 'register'>('login')

const redirectTarget = computed(() => (typeof route.query.redirect === 'string' ? route.query.redirect : '/'))
const submitLabel = computed(() => (mode.value === 'login' ? '进入工作台' : '注册并进入'))

async function submitLogin() {
  if (mode.value === 'login') {
    await auth.loginWithPassword({ account: form.account, password: form.password })
  } else {
    await auth.registerWithPassword({
      email: form.email,
      password: form.password,
      username: form.username,
    })
  }
  await router.replace(redirectTarget.value)
}
</script>

<template>
  <main class="grid min-h-screen place-items-center bg-canvas px-4 py-8 text-ink">
    <section class="grid w-full max-w-960px grid-cols-[minmax(0,1fr)_360px] overflow-hidden border border-line rounded-2 bg-surface max-md:grid-cols-1">
      <div class="min-w-0 border-r border-line p-8 max-md:border-b max-md:border-r-0 max-md:p-5">
        <span class="inline-flex h-42px w-42px items-center justify-center rounded-2 bg-primary text-white text-12px font-800">WHU</span>
        <h1 class="mb-3 mt-6 text-ink text-30px font-800 leading-[1.2]">登录智能文件平台</h1>
        <p class="m-0 max-w-560px text-sub text-15px leading-[1.65]">
          进入文件管理、知识库问答、智能体工具流和团队协作工作台。受保护 API 将携带 JWT 鉴权，并在文件、知识库、工具和团队资源访问前执行权限前置。
        </p>

        <div class="mt-6 grid grid-cols-3 gap-3 max-sm:grid-cols-1">
          <div class="border border-line rounded-2 bg-muted p-3">
            <strong class="block text-ink text-14px">JWT 鉴权</strong>
            <span class="mt-1 block text-sub text-12px leading-[1.5]">登录后签发访问令牌和刷新令牌</span>
          </div>
          <div class="border border-line rounded-2 bg-muted p-3">
            <strong class="block text-ink text-14px">权限前置</strong>
            <span class="mt-1 block text-sub text-12px leading-[1.5]">资源访问先经过身份和 RBAC 校验</span>
          </div>
          <div class="border border-line rounded-2 bg-muted p-3">
            <strong class="block text-ink text-14px">审计追踪</strong>
            <span class="mt-1 block text-sub text-12px leading-[1.5]">关键操作写入审计日志</span>
          </div>
        </div>
      </div>

      <NForm class="grid content-center gap-4 p-6 max-md:p-5" @submit.prevent="submitLogin">
        <NRadioGroup v-model:value="mode" name="auth-mode" button-style="solid">
          <NRadioButton value="login" label="账号登录" />
          <NRadioButton value="register" label="注册账号" />
        </NRadioGroup>

        <NFormItem v-if="mode === 'register'" label="用户名" path="username">
          <NInput v-model:value="form.username" autocomplete="username" placeholder="3-50 位用户名" />
        </NFormItem>
        <NFormItem v-if="mode === 'register'" label="邮箱" path="email">
          <NInput v-model:value="form.email" autocomplete="email" placeholder="用于登录和通知" />
        </NFormItem>
        <NFormItem v-if="mode === 'login'" label="账号" path="account">
          <NInput v-model:value="form.account" autocomplete="username" placeholder="用户名或邮箱" />
        </NFormItem>
        <NFormItem label="密码" path="password">
          <NInput
            v-model:value="form.password"
            autocomplete="current-password"
            placeholder="请输入密码"
            show-password-on="click"
            type="password"
          />
        </NFormItem>
        <NAlert v-if="auth.errorMessage" type="error" :bordered="false">
          {{ auth.errorMessage }}
        </NAlert>
        <NButton attr-type="submit" type="primary" :loading="auth.loading" block>
          <template #icon>
            <NIcon aria-hidden="true"><LogIn /></NIcon>
          </template>
          {{ submitLabel }}
        </NButton>
      </NForm>
    </section>
  </main>
</template>
