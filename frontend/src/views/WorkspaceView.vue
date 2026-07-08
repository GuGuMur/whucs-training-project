<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import AgentWorkflowPanel from '@/components/workspace/AgentWorkflowPanel.vue'
import FileWorkbench from '@/components/workspace/FileWorkbench.vue'
import RagInsightPanel from '@/components/workspace/RagInsightPanel.vue'
import SummaryStrip from '@/components/workspace/SummaryStrip.vue'
import TeamAuditPanel from '@/components/workspace/TeamAuditPanel.vue'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspace = useWorkspaceStore()
const { apiState, auditLogs, files, narrative, summary, teams, tools, workflows } = storeToRefs(workspace)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState)
const workspaceLayout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

onMounted(() => {
  void workspace.loadWorkspace()
})
</script>

<template>
  <component
    :is="workspaceLayout"
    :api-state-label="apiStateLabel"
    :api-state-type="apiStateType"
    :nav-items="navItems"
    :unread-notifications="summary.unread_notifications"
  >
    <SummaryStrip :summary="summary" />

    <div class="mt-4 grid grid-cols-[minmax(0,1.55fr)_minmax(320px,0.9fr)] gap-4 max-xl:grid-cols-1">
      <div class="grid content-start gap-4 min-w-0">
        <FileWorkbench id="files" :files="files" />
        <AgentWorkflowPanel
          id="automation"
          :agent-steps="narrative.agentSteps"
          :tools="tools"
          :workflows="workflows"
        />
      </div>

      <div class="grid content-start gap-4 min-w-0">
        <RagInsightPanel id="rag" :narrative="narrative" />
        <TeamAuditPanel id="teams" :teams="teams" :audit-logs="auditLogs" />
      </div>
    </div>
  </component>
</template>
