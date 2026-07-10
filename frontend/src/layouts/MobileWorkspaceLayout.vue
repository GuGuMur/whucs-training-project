<script setup lang="ts">
import { computed } from 'vue'
import { Bell, LogOut, MessageSquareText, ShieldCheck, UserPlus, UserRound, Workflow } from '@lucide/vue'
import { useRouter } from 'vue-router'

import type { WorkspaceNavItem } from '@/composables/useWorkspaceNavigation'
import type { WorkspaceNotification } from '@/client/workspace'
import { useAuthStore } from '@/stores/auth'

const props = withDefaults(defineProps<{
  apiStateLabel: string
  apiStateType: 'success' | 'warning' | 'info'
  navItems: WorkspaceNavItem[]
  pageTitle?: string
  unreadNotifications: number
  notifications?: WorkspaceNotification[]
  markingNotificationId?: string | null
}>(), {
  notifications: () => [],
  markingNotificationId: null,
})

const emit = defineEmits<{
  'mark-notification-read': [notificationId: string]
}>()

const auth = useAuthStore()
const router = useRouter()

const avatarLetter = computed(() => {
  const name = auth.currentUser?.display_name || auth.currentUser?.username || '?'
  return (name[0] ?? "?").toUpperCase()
})

function handleNotificationClick(notification: WorkspaceNotification) {
  if (!notification.is_read) {
    emit('mark-notification-read', notification.id)
  }
  switch (notification.type) {
    case 'annotation': router.push('/files'); break
    case 'invite': router.push('/team-chat'); break
    case 'mention': router.push('/team-chat'); break
    case 'workflow': router.push('/workflow'); break
  }
}

function notificationTypeLabel(type: WorkspaceNotification['type']) {
  const labels: Record<string, string> = { annotation: '批注', invite: '邀请', mention: '提醒', workflow: '流程', system: '系统' }
  return labels[type] ?? type
}

function notificationIcon(type: WorkspaceNotification['type']) {
  switch (type) {
    case 'annotation': return MessageSquareText
    case 'invite': return UserPlus
    case 'mention': return Bell
    case 'workflow': return Workflow
    default: return Bell
  }
}

function handleLogout() { auth.logout(); router.push('/login') }
</script>

<template>
  <main class="min-h-screen bg-canvas text-ink">
    <header class="sticky top-0 z-2 border-b border-line bg-surface px-4 py-3" aria-label="移动端导航">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="inline-flex h-34px w-34px items-center justify-center rounded-2 bg-primary text-white text-11px font-800">WHU</span>
          <strong class="text-ink text-14px font-800">智能文件平台</strong>
        </div>
        <div class="flex items-center gap-2">
          <NTag :type="apiStateType" size="small" round>{{ apiStateLabel }}</NTag>

          <!-- Mobile notification bell -->
          <NPopover trigger="click" placement="bottom-end" :show-arrow="false" :width="300">
            <template #trigger>
              <div class="relative flex h-30px w-30px cursor-pointer items-center justify-center rounded-full bg-muted text-sub transition-colors hover:bg-primarySoft hover:text-primary">
                <NIcon :size="16"><Bell /></NIcon>
                <span
                  v-if="unreadNotifications"
                  class="absolute -top-0.5 -right-0.5 flex h-16px min-w-16px items-center justify-center rounded-full bg-danger px-1 text-9px text-white font-700"
                >{{ unreadNotifications > 99 ? '99+' : unreadNotifications }}</span>
              </div>
            </template>
            <div class="grid max-h-320px overflow-y-auto">
              <div class="sticky top-0 z-1 flex items-center justify-between border-b border-line bg-surface px-3 py-2">
                <span class="text-ink text-13px font-700">通知中心</span>
                <NBadge v-if="unreadNotifications" :value="unreadNotifications" type="error" />
              </div>
              <NEmpty v-if="!notifications.length" size="small" description="暂无通知" class="py-6" />
              <button
                v-for="notification in notifications"
                :key="notification.id"
                class="flex items-start gap-2 border-b border-line px-3 py-2.5 text-left transition-colors hover:bg-primarySoft border-none bg-transparent w-full cursor-pointer"
                :class="notification.is_read ? 'opacity-60' : ''"
                @click="handleNotificationClick(notification)"
              >
                <span class="mt-0.5 flex h-24px w-24px shrink-0 items-center justify-center rounded-full" :class="notification.is_read ? 'bg-muted text-sub' : 'bg-primarySoft text-primary'">
                  <NIcon :size="12"><component :is="notificationIcon(notification.type)" /></NIcon>
                </span>
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-1.5">
                    <span class="truncate text-ink text-12px font-650">{{ notification.title }}</span>
                    <span v-if="!notification.is_read" class="h-5px w-5px shrink-0 rounded-full bg-primary"></span>
                  </div>
                  <p class="m-0 mt-0.5 line-clamp-2 text-sub text-11px leading-[1.5]">{{ notification.content || '暂无正文' }}</p>
                  <span class="mt-0.5 inline-block text-sub text-10px">{{ notificationTypeLabel(notification.type) }}</span>
                </div>
              </button>
            </div>
          </NPopover>

          <RouterLink to="/profile">
            <div class="flex h-30px w-30px items-center justify-center rounded-full bg-primary text-white text-12px font-700">
              {{ avatarLetter }}
            </div>
          </RouterLink>
        </div>
      </div>

      <nav :class="`mt-2.5 grid gap-1`" :style="`grid-template-columns: repeat(${navItems.length}, minmax(0, 1fr))`">
        <RouterLink
          v-for="item in navItems"
          :key="item.to ?? item.href"
          class="flex min-h-44px flex-col items-center justify-center gap-0.5 rounded-1.5 px-1 text-11px font-650 no-underline transition-colors hover:bg-primarySoft hover:text-primary"
          :class="item.active ? 'bg-primarySoft text-primary' : 'text-sub'"
          :to="item.to ?? ''"
          :aria-label="item.label"
        >
          <NIcon :size="18" aria-hidden="true"><component :is="item.icon" /></NIcon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </header>

    <section class="min-w-0 px-4 py-4">
      <slot />
    </section>
  </main>
</template>
