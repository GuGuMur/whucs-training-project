import { createAuthorizationHeader } from '@/auth/workspaceAccess'
import { workspaceSnapshotApiV1WorkspaceSnapshotGet } from '@/client/generated'
import type {
  AgentStep as GeneratedAgentStep,
  AuditLogEntry,
  Citation,
  DashboardSummary,
  FileItem,
  TeamSummary,
  ToolDefinition,
  WorkflowDefinition,
  WorkspaceSnapshot,
} from '@/client/generated'

export type AgentStep = GeneratedAgentStep & { status: NonNullable<GeneratedAgentStep['status']> }
export type WorkspaceFile = FileItem
export type {
  AuditLogEntry,
  Citation,
  DashboardSummary,
  TeamSummary,
  ToolDefinition,
  WorkflowDefinition,
  WorkspaceSnapshot,
}

export interface WorkspaceNarrative {
  answer: string
  citations: Citation[]
  agentSteps: AgentStep[]
}

export const demoWorkspaceSnapshot: WorkspaceSnapshot = {
  summary: {
    file_count: 3,
    indexed_count: 2,
    knowledge_base_count: 2,
    running_workflows: 0,
    unread_notifications: 4,
    tools_enabled: 4,
  },
  files: [
    {
      id: 'file-microscope',
      name: '显微镜实验报告.pdf',
      folder_id: 'folder-biology',
      type: 'pdf',
      size: 2430112,
      sha256: '8b73c9d2d4c02b4b4f0e1c7a8dbf1023f44e8d9e7a10f24b15a02d983ff42d91',
      parse_status: 'indexed',
      tags: ['实验', '显微镜'],
      updated_at: '2026-07-08T06:21:00+08:00',
      permission_scope: '个人',
      knowledge_base_ids: ['kb-biology'],
    },
    {
      id: 'file-requirements',
      name: '需求规格说明书.md',
      folder_id: 'folder-course',
      type: 'markdown',
      size: 96418,
      sha256: 'fb8bd33418f0d6a73f83341f1f3bbef710c66f6a73e4c4afece8e7dfcb71b884',
      parse_status: 'indexed',
      tags: ['课程', '需求'],
      updated_at: '2026-07-07T18:10:00+08:00',
      permission_scope: '团队',
      knowledge_base_ids: ['kb-course'],
    },
    {
      id: 'file-weekly',
      name: '小组周报.docx',
      folder_id: 'team-root',
      type: 'docx',
      size: 384200,
      sha256: 'd654611a21f65bbdcad7f0c96da59e267674b0d806f65220b46fbf35d94a826b',
      parse_status: 'parsing',
      tags: ['周报', '团队'],
      updated_at: '2026-07-08T07:43:00+08:00',
      permission_scope: '团队',
      knowledge_base_ids: [],
    },
  ],
  tools: [
    {
      id: 'tool-file-search',
      name: 'file_search',
      version: '1.0.0',
      category: '文件操作',
      description: '按文件名、标签和解析状态搜索用户可访问文件。',
      input_schema: { type: 'object', properties: { query: { type: 'string' } } },
      output_schema: { type: 'object', properties: { files: { type: 'array' } } },
      enabled: true,
    },
    {
      id: 'tool-knowledge-qa',
      name: 'knowledge_qa',
      version: '1.0.0',
      category: 'AI处理',
      description: '基于知识库检索片段生成带引用的回答。',
      input_schema: { type: 'object', properties: { question: { type: 'string' }, kb_id: { type: 'string' } } },
      output_schema: { type: 'object', properties: { answer: { type: 'string' }, citations: { type: 'array' } } },
      enabled: true,
    },
    {
      id: 'tool-report-generate',
      name: 'report_generate',
      version: '1.0.0',
      category: 'AI处理',
      description: '将检索结果和活动动态整理为 Markdown 报告。',
      input_schema: { type: 'object', properties: { file_ids: { type: 'array' } } },
      output_schema: { type: 'object', properties: { markdown: { type: 'string' } } },
      enabled: true,
    },
    {
      id: 'tool-image-ocr',
      name: 'image_ocr',
      version: '1.0.0',
      category: '文档解析',
      description: '提取图片或扫描件中的文字。',
      input_schema: { type: 'object', properties: { image_file_id: { type: 'string' } } },
      output_schema: { type: 'object', properties: { text: { type: 'string' } } },
      enabled: true,
    },
  ],
  workflows: [
    {
      id: 'new-file-auto-summary',
      name: '新文件自动摘要',
      description: '文件上传后自动解析、知识库问答并生成摘要。',
      trigger: 'file.uploaded',
      version: '1.0.0',
      node_count: 3,
      status: 'published',
    },
  ],
  teams: [
    { id: 'team-biology', name: '生物学实验', role: '团队管理员', member_count: 6, unread_count: 3 },
    { id: 'team-course', name: '软件工程课程组', role: '成员', member_count: 5, unread_count: 1 },
  ],
  audit_logs: [
    {
      id: 'audit-1',
      actor: 'xiaoming',
      action: 'workflow.execute',
      resource_type: 'workflow',
      resource_name: 'new-file-auto-summary',
      created_at: '2026-07-08T08:10:00+08:00',
    },
    {
      id: 'audit-2',
      actor: 'system',
      action: 'tool.publish',
      resource_type: 'tool',
      resource_name: 'knowledge_qa',
      created_at: '2026-07-08T04:20:00+08:00',
    },
  ],
}

export const demoWorkspaceNarrative: WorkspaceNarrative = {
  answer:
    '显微镜相关实验步骤包括：准备载玻片与样本，低倍镜定位目标区域，切换高倍镜观察细胞结构，记录视野特征，并在实验报告中附上观察结论。',
  citations: [
    {
      file_id: 'file-microscope',
      document_id: 'doc-microscope',
      chunk_id: 'chunk-micro-003',
      title: '显微镜实验报告.pdf',
      page_no: 3,
      paragraph_no: 5,
      snippet: '显微镜实验包含取样、制片、低倍镜定位、高倍镜观察和结果记录。',
    },
  ],
  agentSteps: [
    { type: 'thought', title: '任务理解', content: '需要先定位相关文件，再生成结构化报告。', status: 'success' },
    {
      type: 'action',
      title: '搜索文件',
      content: '按生物实验和显微镜关键词检索文件。',
      tool_name: 'file_search',
      status: 'success',
    },
    { type: 'observation', title: '文件结果', content: '找到 显微镜实验报告.pdf，已入库。', status: 'success' },
    {
      type: 'action',
      title: '生成报告',
      content: '根据检索结果生成团队周报草稿。',
      tool_name: 'report_generate',
      status: 'success',
    },
    { type: 'answer', title: '最终结果', content: '报告草稿已生成，包含实验目的、步骤、观察结果和待确认事项。', status: 'success' },
  ],
}

export async function fetchWorkspaceSnapshot(token: string): Promise<WorkspaceSnapshot> {
  const response = await workspaceSnapshotApiV1WorkspaceSnapshotGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}
