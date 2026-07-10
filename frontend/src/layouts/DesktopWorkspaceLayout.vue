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
    case 'annotation':
      router.push('/files')
      break
    case 'invite':
      router.push('/team-chat')
      break
    case 'mention':
      router.push('/team-chat')
      break
    case 'workflow':
      router.push('/workflow')
      break
    default:
      break
  }
}

function notificationTypeLabel(type: WorkspaceNotification['type']) {
  const labels: Record<string, string> = {
    annotation: '批注',
    invite: '邀请',
    mention: '提醒',
    workflow: '流程',
    system: '系统',
  }
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

function handleProfile() { router.push('/profile') }
function handleAudit() { router.push('/permission-audit') }
function handleLogout() { auth.logout(); router.push('/login') }
</script>

<template>
  <main class="grid h-screen grid-cols-[248px_minmax(0,1fr)] bg-canvas text-ink max-xl:grid-cols-[74px_minmax(0,1fr)] overflow-hidden">
    <!-- Fixed sidebar with independent scroll -->
    <aside class="flex flex-col border-r border-line bg-surface px-4 py-4.5 overflow-y-auto" aria-label="主导航">
      <div class="flex min-h-10 items-center gap-2.5">
        <span class="inline-flex h-38px w-38px shrink-0 items-center justify-center rounded-2 bg-primary text-white text-12px font-800">WHU</span>
        <strong class="truncate text-ink text-15px font-800 max-xl:hidden">智能文件平台</strong>
      </div>
      <nav class="mt-6 grid gap-1.5">
        <RouterLink
          v-for="item in navItems"
          :key="item.to ?? item.href"
          class="flex min-h-40px items-center gap-2.5 rounded-1.5 px-3 text-14px font-650 no-underline transition-colors hover:bg-primarySoft hover:text-primary max-xl:justify-center max-xl:px-0"
          :class="item.active ? 'bg-primarySoft text-primary' : 'text-sub'"
          :to="item.to ?? ''"
          :aria-label="item.label"
        >
          <NIcon :size="18" aria-hidden="true"><component :is="item.icon" /></NIcon>
          <span class="max-xl:hidden">{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <!-- Content area with independent scroll -->
    <section class="flex flex-col min-w-0 overflow-y-auto">
      <!-- Sticky top bar -->
      <header class="sticky top-0 z-2 flex items-center justify-between gap-5 border-b border-line bg-surface px-6 py-3">
        <h1 class="m-0 text-ink text-17px font-700">{{ pageTitle ?? '文件管理' }}</h1>
        <div class="flex items-center gap-2.5">
          <NTag :type="apiStateType" size="small" round>{{ apiStateLabel }}</NTag>

          <!-- Notification bell -->
          <NPopover trigger="click" placement="bottom-end" :show-arrow="false" :width="320">
            <template #trigger>
              <div class="relative flex h-34px w-34px cursor-pointer items-center justify-center rounded-full bg-muted text-sub transition-colors hover:bg-primarySoft hover:text-primary">
                <NIcon :size="18"><Bell /></NIcon>
                <span
                  v-if="unreadNotifications"
                  class="absolute -top-0.5 -right-0.5 flex h-18px min-w-18px items-center justify-center rounded-full bg-danger px-1 text-10px text-white font-700"
                >{{ unreadNotifications > 99 ? '99+' : unreadNotifications }}</span>
              </div>
            </template>
            <div class="grid max-h-360px overflow-y-auto">
              <div class="sticky top-0 z-1 flex items-center justify-between border-b border-line bg-surface px-4 py-2.5">
                <span class="text-ink text-14px font-700">通知中心</span>
                <NBadge v-if="unreadNotifications" :value="unreadNotifications" type="error" />
              </div>
              <NEmpty v-if="!notifications.length" size="small" description="暂无通知" class="py-8" />
              <button
                v-for="notification in notifications"
                :key="notification.id"
                class="flex items-start gap-2.5 border-b border-line px-4 py-3 text-left transition-colors hover:bg-primarySoft border-none bg-transparent w-full cursor-pointer"
                :class="notification.is_read ? 'opacity-70' : ''"
                @click="handleNotificationClick(notification)"
              >
                <span class="mt-0.5 flex h-28px w-28px shrink-0 items-center justify-center rounded-full" :class="notification.is_read ? 'bg-muted text-sub' : 'bg-primarySoft text-primary'">
                  <NIcon :size="14"><component :is="notificationIcon(notification.type)" /></NIcon>
                </span>
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <span class="truncate text-ink text-13px font-650">{{ notification.title }}</span>
                    <span v-if="!notification.is_read" class="h-6px w-6px shrink-0 rounded-full bg-primary"></span>
                  </div>
                  <p class="m-0 mt-0.5 line-clamp-2 text-sub text-12px leading-[1.5]">{{ notification.content || '暂无正文' }}</p>
                  <span class="mt-1 inline-block text-sub text-11px">{{ notificationTypeLabel(notification.type) }}</span>
                </div>
              </button>
            </div>
          </NPopover>

          <!-- User avatar + dropdown menu -->
          <NPopover trigger="click" placement="bottom-end" :show-arrow="false">
            <template #trigger>
              <div class="flex h-34px w-34px cursor-pointer items-center justify-center rounded-full bg-primary text-white text-14px font-700 select-none hover:opacity-85">
                {{ avatarLetter }}
              </div>
            </template>
            <div class="grid w-200px gap-1 py-2">
              <div class="px-3 pb-2 border-b border-line">
                <p class="m-0 text-ink text-14px font-650">{{ auth.currentUser?.display_name || auth.currentUser?.username }}</p>
                <p class="m-0 text-sub text-12px">{{ auth.currentUser?.email }}</p>
              </div>
              <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-14px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="handleProfile">
                <NIcon :size="16"><UserRound /></NIcon>
                <span>个人资料</span>
              </button>
              <button v-if="auth.isAdmin" class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-14px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="handleAudit">
                <NIcon :size="16"><ShieldCheck /></NIcon>
                <span>权限审计</span>
              </button>
              <div class="mt-1 border-t border-line pt-1">
                <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-14px text-danger transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="handleLogout">
                  <NIcon :size="16"><LogOut /></NIcon>
                  <span>退出登录</span>
                </button>
              </div>
            </div>
          </NPopover>
        </div>
      </header>

      <!-- Page slot -->
      <div class="px-6 py-4">
        <slot />
      </div>
    </section>
  </main>
</template>
