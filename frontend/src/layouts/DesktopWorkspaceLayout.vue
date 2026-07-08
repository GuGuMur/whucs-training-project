<script setup lang="ts">
import { Bell, Plus, UserRound } from '@lucide/vue'

import type { WorkspaceNavItem } from '@/composables/useWorkspaceNavigation'

defineProps<{
  apiStateLabel: string
  apiStateType: 'success' | 'warning' | 'info'
  navItems: WorkspaceNavItem[]
  unreadNotifications: number
}>()
</script>

<template>
  <main class="grid min-h-screen grid-cols-[248px_minmax(0,1fr)] bg-canvas text-ink max-xl:grid-cols-[74px_minmax(0,1fr)]">
    <aside class="border-r border-line bg-surface px-4 py-4.5" aria-label="主导航">
      <div class="flex min-h-10 items-center gap-2.5">
        <span class="inline-flex h-38px w-38px items-center justify-center rounded-2 bg-primary text-white text-12px font-800">WHU</span>
        <strong class="text-ink text-15px font-800 max-xl:hidden">智能文件平台</strong>
      </div>
      <nav class="mt-6 grid gap-1.5">
        <template v-for="item in navItems" :key="item.to ?? item.href">
          <RouterLink
            v-if="item.to"
            class="flex min-h-40px items-center gap-2.5 rounded-1.5 px-3 text-14px font-650 no-underline transition-colors hover:bg-primarySoft hover:text-primary max-xl:justify-center max-xl:px-0"
            :class="item.active ? 'bg-primarySoft text-primary' : 'text-sub'"
            :to="item.to"
            :aria-label="item.label"
          >
            <NIcon :size="18" aria-hidden="true">
              <component :is="item.icon" />
            </NIcon>
            <span class="max-xl:hidden">{{ item.label }}</span>
          </RouterLink>
          <a
            v-else
            class="flex min-h-40px items-center gap-2.5 rounded-1.5 px-3 text-14px font-650 no-underline transition-colors hover:bg-primarySoft hover:text-primary max-xl:justify-center max-xl:px-0"
            :class="item.active ? 'bg-primarySoft text-primary' : 'text-sub'"
            :href="item.href"
            :aria-label="item.label"
          >
            <NIcon :size="18" aria-hidden="true">
              <component :is="item.icon" />
            </NIcon>
            <span class="max-xl:hidden">{{ item.label }}</span>
          </a>
        </template>
      </nav>
    </aside>

    <section class="min-w-0 px-6 py-5.5">
      <header class="mb-4 flex items-start justify-between gap-5">
        <div>
          <p class="m-0 mb-1.5 text-sub text-13px">软件工程课程组 · 个人空间</p>
          <h1 class="m-0 text-ink text-30px font-800 leading-[1.2]">智能文件工作台</h1>
        </div>
        <NSpace :size="10" align="center" class="justify-end">
          <NTag :type="apiStateType" round>数据源：{{ apiStateLabel }}</NTag>
          <NButton secondary>
            <template #icon>
              <NIcon aria-hidden="true"><Bell /></NIcon>
            </template>
            通知 {{ unreadNotifications }}
          </NButton>
          <RouterLink class="btn-secondary no-underline" to="/profile">
            <NIcon aria-hidden="true" class="mr-1.5"><UserRound /></NIcon>
            个人资料
          </RouterLink>
          <NButton type="primary">
            <template #icon>
              <NIcon aria-hidden="true"><Plus /></NIcon>
            </template>
            创建知识库
          </NButton>
        </NSpace>
      </header>

      <slot />
    </section>
  </main>
</template>
