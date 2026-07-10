import { createRouter, createWebHistory, type RouterHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import FileManagerView from '@/views/FileManagerView.vue'
import LoginView from '@/views/LoginView.vue'
import PermissionAuditView from '@/views/PermissionAuditView.vue'
import ProfileView from '@/views/ProfileView.vue'
import RagQaView from '@/views/RagQaView.vue'
import TeamChatView from '@/views/TeamChatView.vue'
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
        redirect: '/files',
      },
      {
        path: '/files',
        name: 'files',
        component: FileManagerView,
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

  let tokenValidated = false

  router.beforeEach(async (to) => {
    const auth = useAuthStore()

    // Restore from localStorage if not already authenticated
    const wasRestored = !auth.isAuthenticated
    if (wasRestored) {
      auth.restoreLocalSession()
    }

    // Validate restored token against server (runs once per app load)
    if (to.meta.requiresAuth && auth.isAuthenticated && wasRestored && !tokenValidated) {
      tokenValidated = true
      await auth.restoreSession().catch(() => {})
    }

    // For protected routes without a session, redirect to login
    if (to.meta.requiresAuth && !auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    if (to.meta.requiresAdmin && !auth.isAdmin) {
      return { name: 'files' }
    }

    if (to.meta.guestOnly && auth.isAuthenticated) {
      return { name: 'files' }
    }
  })

  return router
}

const router = createAppRouter()

export default router
