<script setup lang="ts">
import { computed, onMounted, reactive, shallowRef, watch } from 'vue'
import { ArrowLeft, Save, ShieldCheck } from '@lucide/vue'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const savedNotice = shallowRef('')

const form = reactive({
  display_name: '',
  email: '',
})

const roleLabel = computed(() => auth.roles.join(' / ') || 'user')

watch(
  () => auth.currentUser,
  (user) => {
    form.display_name = user?.display_name ?? auth.session?.displayName ?? ''
    form.email = user?.email ?? ''
  },
  { immediate: true },
)

onMounted(() => {
  if (!auth.currentUser) {
    void auth.restoreSession()
  }
})

async function submitProfile() {
  savedNotice.value = ''
  await auth.updateProfile({
    display_name: form.display_name,
    email: form.email,
  })
  savedNotice.value = '个人资料已更新'
}
</script>

<template>
  <main class="min-h-screen bg-canvas px-4 py-5 text-ink">
    <section class="mx-auto grid max-w-920px gap-4">
      <RouterLink class="btn-secondary w-fit no-underline" to="/">
        <NIcon aria-hidden="true" class="mr-1.5"><ArrowLeft /></NIcon>
        返回工作台
      </RouterLink>

      <section class="app-panel overflow-hidden">
        <div class="border-b border-line bg-surface px-5 py-4">
          <p class="m-0 mb-1.5 text-sub text-13px">账号与权限</p>
          <h1 class="m-0 text-ink text-28px font-800 leading-[1.2]">个人资料</h1>
        </div>

        <div class="grid grid-cols-[minmax(0,0.9fr)_minmax(320px,1.1fr)] gap-0 max-md:grid-cols-1">
          <aside class="border-r border-line bg-muted p-5 max-md:border-b max-md:border-r-0">
            <div class="flex items-start gap-3">
              <span class="inline-flex h-46px w-46px items-center justify-center rounded-2 bg-primary text-white text-14px font-800">
                {{ auth.displayName.slice(0, 2) }}
              </span>
              <div class="min-w-0">
                <strong class="block truncate text-ink text-16px">{{ auth.displayName }}</strong>
                <span class="mt-1 block text-sub text-13px">{{ auth.currentUser?.username }}</span>
              </div>
            </div>

            <div class="mt-5 grid gap-2.5">
              <div class="rounded-2 border border-line bg-surface p-3">
                <span class="block text-sub text-12px">登录邮箱</span>
                <strong class="mt-1 block break-all text-ink text-14px">{{ auth.currentUser?.email }}</strong>
              </div>
              <div class="rounded-2 border border-line bg-surface p-3">
                <span class="block text-sub text-12px">权限角色</span>
                <strong class="mt-1 flex items-center gap-1.5 text-ink text-14px">
                  <NIcon aria-hidden="true"><ShieldCheck /></NIcon>
                  {{ roleLabel }}
                </strong>
              </div>
            </div>
          </aside>

          <NForm class="grid gap-3 p-5" @submit.prevent="submitProfile">
            <NFormItem label="显示名称" path="display_name">
              <NInput v-model:value="form.display_name" placeholder="例如：小明同学" />
            </NFormItem>
            <NFormItem label="邮箱" path="email">
              <NInput v-model:value="form.email" autocomplete="email" placeholder="用于登录和系统通知" />
            </NFormItem>

            <NAlert v-if="auth.errorMessage" type="error" :bordered="false">
              {{ auth.errorMessage }}
            </NAlert>
            <NAlert v-if="savedNotice" type="success" :bordered="false">
              {{ savedNotice }}
            </NAlert>

            <NButton attr-type="submit" type="primary" :loading="auth.loading">
              <template #icon>
                <NIcon aria-hidden="true"><Save /></NIcon>
              </template>
              保存资料
            </NButton>
          </NForm>
        </div>
      </section>
    </section>
  </main>
</template>
