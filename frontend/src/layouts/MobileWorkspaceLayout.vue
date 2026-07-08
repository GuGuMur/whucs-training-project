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
  <main class="min-h-screen bg-canvas text-ink">
    <header class="sticky top-0 z-2 border-b border-line bg-surface px-4 py-4" aria-label="移动端工作台导航">
      <div class="flex items-center gap-2.5">
        <span class="inline-flex h-38px w-38px items-center justify-center rounded-2 bg-primary text-white text-12px font-800">WHU</span>
        <strong class="text-ink text-15px font-800">智能文件平台</strong>
      </div>

      <nav class="mt-3 grid grid-cols-5 gap-1.5">
        <a
          v-for="item in navItems"
          :key="item.href"
          class="flex min-h-48px flex-col items-center justify-center gap-1 rounded-1.5 px-1 text-12px font-650 no-underline transition-colors hover:bg-primarySoft hover:text-primary"
          :class="item.active ? 'bg-primarySoft text-primary' : 'text-sub'"
          :href="item.href"
          :aria-label="item.label"
        >
          <NIcon :size="20" aria-hidden="true">
            <component :is="item.icon" />
          </NIcon>
          <span>{{ item.label }}</span>
        </a>
      </nav>
    </header>

    <section class="min-w-0 px-4 py-4">
      <div class="mb-4">
        <p class="m-0 mb-1.5 text-sub text-13px">软件工程课程组 · 个人空间</p>
        <h1 class="m-0 text-ink text-30px font-800 leading-[1.2]">智能文件工作台</h1>
        <NSpace :size="10" class="mt-4" align="center">
          <NTag :type="apiStateType" round>数据源：{{ apiStateLabel }}</NTag>
          <NButton secondary>
            <template #icon>
              <NIcon aria-hidden="true"><Bell /></NIcon>
            </template>
            通知 {{ unreadNotifications }}
          </NButton>
          <RouterLink class="btn-secondary no-underline" to="/profile">
            <NIcon aria-hidden="true" class="mr-1.5"><UserRound /></NIcon>
            资料
          </RouterLink>
          <NButton type="primary">
            <template #icon>
              <NIcon aria-hidden="true"><Plus /></NIcon>
            </template>
            创建知识库
          </NButton>
        </NSpace>
      </div>

      <slot />
    </section>
  </main>
</template>
