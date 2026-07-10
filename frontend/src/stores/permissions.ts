import { shallowRef } from 'vue'
import { defineStore } from 'pinia'

import { requireAccessToken, resolveOptionalAccessToken } from '@/auth'
import {
  createWorkspacePermissionRule,
  deleteWorkspacePermissionRule,
  listWorkspacePermissionRules,
  type WorkspacePermissionRule,
  type WorkspacePermissionRuleCreateInput,
} from '@/client/workspace'

export const usePermissionsStore = defineStore('permissions', () => {
  const permissionRules = shallowRef<WorkspacePermissionRule[]>([])
  const permissionRulesLoading = shallowRef(false)
  const permissionRuleSaving = shallowRef(false)
  const deletingPermissionRuleId = shallowRef<string | null>(null)

  const errorMessage = shallowRef('')

  // ── Actions ──

  async function loadPermissionRules(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      return { items: permissionRules.value }
    }

    permissionRulesLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listWorkspacePermissionRules(accessToken)
      permissionRules.value = clonePermissionRules(response.items)
      return response
    } catch (error) {
      errorMessage.value = '权限规则加载失败，请稍后重试'
      throw error
    } finally {
      permissionRulesLoading.value = false
    }
  }

  async function createPermissionRule(payload: WorkspacePermissionRuleCreateInput) {
    const accessToken = requireAccessToken()
    const nextPayload = normalizePermissionRulePayload(payload)

    permissionRuleSaving.value = true
    errorMessage.value = ''
    try {
      const created = await createWorkspacePermissionRule(accessToken, nextPayload)
      upsertPermissionRule(created, true)
      return created
    } catch (error) {
      errorMessage.value = '权限规则保存失败，请检查主体、资源和管理权限'
      throw error
    } finally {
      permissionRuleSaving.value = false
    }
  }

  async function deletePermissionRule(ruleId: string) {
    const accessToken = requireAccessToken()

    deletingPermissionRuleId.value = ruleId
    errorMessage.value = ''
    try {
      await deleteWorkspacePermissionRule(accessToken, ruleId)
      permissionRules.value = permissionRules.value.filter((rule) => rule.id !== ruleId)
    } catch (error) {
      errorMessage.value = '权限规则删除失败，请检查管理权限'
      throw error
    } finally {
      deletingPermissionRuleId.value = null
    }
  }

  // ── Helpers ──

  function upsertPermissionRule(rule: WorkspacePermissionRule, moveToFront = false) {
    const existing = permissionRules.value.some((item) => item.id === rule.id)
    permissionRules.value = moveToFront
      ? [rule, ...permissionRules.value.filter((item) => item.id !== rule.id)]
      : existing
        ? permissionRules.value.map((item) => (item.id === rule.id ? rule : item))
        : [rule, ...permissionRules.value]
  }

  return {
    // state
    permissionRules,
    permissionRulesLoading,
    permissionRuleSaving,
    deletingPermissionRuleId,
    errorMessage,
    // actions
    loadPermissionRules,
    createPermissionRule,
    deletePermissionRule,
  }
})

// ── Module-level helpers ──

function clonePermissionRules(rules: WorkspacePermissionRule[]): WorkspacePermissionRule[] {
  return rules.map((rule) => ({ ...rule }))
}

function normalizePermissionRulePayload(payload: WorkspacePermissionRuleCreateInput): WorkspacePermissionRuleCreateInput {
  return {
    action: payload.action,
    effect: payload.effect,
    inherit: payload.inherit ?? false,
    resourceId: payload.resourceId.trim(),
    resourceType: payload.resourceType,
    subjectId: payload.subjectId.trim(),
    subjectType: payload.subjectType,
  }
}
