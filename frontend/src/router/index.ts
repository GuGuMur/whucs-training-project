import { createRouter, createWebHistory, type RouterHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import PermissionAuditView from '@/views/PermissionAuditView.vue'
import ProfileView from '@/views/ProfileView.vue'
import RagQaView from '@/views/RagQaView.vue'
import TeamChatView from '@/views/TeamChatView.vue'
import WorkspaceView from '@/views/WorkspaceView.vue'
import WorkflowBuilderView from '@/views/WorkflowBuilderView.vue'

export function createAppRouter(history: RouterHistory = createWebHistory(import.meta.env.BASE_URL)) {
  const router = createRouter({
    history,
    routes: [
      {
        path: '/login',
        name: 'login',
        component: LoginView,
        meta: { guestOnly: true },
      },
      {
        path: '/',
        name: 'workspace',
        component: WorkspaceView,
        meta: { requiresAuth: true },
      },
      {
        path: '/rag',
        name: 'rag-qa',
        component: RagQaView,
        meta: { requiresAuth: true },
      },
      {
        path: '/workflow',
        name: 'workflow-builder',
        component: WorkflowBuilderView,
        meta: { requiresAuth: true },
      },
      {
        path: '/team-chat',
        name: 'team-chat',
        component: TeamChatView,
        meta: { requiresAuth: true },
      },
      {
        path: '/permission-audit',
        name: 'permission-audit',
        component: PermissionAuditView,
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: '/profile',
        name: 'profile',
        component: ProfileView,
        meta: { requiresAuth: true },
      },
    ],
  })

  router.beforeEach((to) => {
    const auth = useAuthStore()
    if (!auth.isAuthenticated) {
      auth.restoreLocalSession()
    }

    if (to.meta.requiresAuth && !auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    if (to.meta.requiresAdmin && !auth.canAccessPermissionAudit) {
      return { name: 'workspace' }
    }

    if (to.meta.guestOnly && auth.isAuthenticated) {
      return { name: 'workspace' }
    }
  })

  return router
}

const router = createAppRouter()

export default router
