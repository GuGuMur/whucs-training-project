<script setup lang="ts">
import { computed } from 'vue'
import { Bell, CheckCircle2 } from '@lucide/vue'

import type { WorkspaceNotification } from '@/client/workspace'

const props = withDefaults(defineProps<{
  markingNotificationId?: string | null
  notifications: WorkspaceNotification[]
  notificationsLoading?: boolean
}>(), {
  markingNotificationId: null,
  notificationsLoading: false,
})

const emit = defineEmits<{
  'mark-notification-read': [notificationId: string]
}>()

const unreadCount = computed(() => props.notifications.filter((item) => !item.is_read).length)

const typeLabels: Record<WorkspaceNotification['type'], string> = {
  annotation: '批注',
  invite: '邀请',
  mention: '提醒',
  system: '系统',
  workflow: '流程',
}

function notificationTypeLabel(type: WorkspaceNotification['type']) {
  return typeLabels[type] ?? type
}
</script>

<template>
  <NCard class="min-w-0 overflow-hidden" size="small">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div class="flex min-w-0 items-center gap-2">
          <NIcon aria-hidden="true"><Bell /></NIcon>
          <span>通知</span>
        </div>
        <NBadge :value="unreadCount" type="info" />
      </div>
    </template>

    <NSpin :show="notificationsLoading">
      <NEmpty v-if="!notifications.length" size="small" description="暂无通知" />
      <NList v-else :show-divider="false">
        <NListItem v-for="notification in notifications" :key="notification.id" class="!px-0 !py-2">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="flex min-w-0 items-center gap-2">
                <NTag size="small" round :bordered="false" :type="notification.is_read ? 'default' : 'info'">
                  {{ notificationTypeLabel(notification.type) }}
                </NTag>
                <p class="m-0 truncate text-ink text-14px font-700">{{ notification.title }}</p>
              </div>
              <p class="m-0 mt-1 line-clamp-2 text-sub text-12px leading-[1.65]">
                {{ notification.content || '暂无通知正文' }}
              </p>
            </div>
            <NButton
              v-if="!notification.is_read"
              :data-testid="'mark-notification-' + notification.id + '-read'"
              size="tiny"
              secondary
              :loading="markingNotificationId === notification.id"
              @click="emit('mark-notification-read', notification.id)"
            >
              <template #icon><NIcon aria-hidden="true"><CheckCircle2 /></NIcon></template>
              已读
            </NButton>
          </div>
        </NListItem>
      </NList>
    </NSpin>
  </NCard>
</template>
