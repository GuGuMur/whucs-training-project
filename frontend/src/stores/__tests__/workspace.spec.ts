import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { saveWorkspaceSession } from '@/auth'
import * as workspaceClient from '@/client/workspace'
import {
  demoWorkspaceSnapshot,
  type WorkspaceNotification,
  type WorkspacePermissionRule,
  type WorkspaceFileVersion,
  type WorkspaceFolder,
  type WorkspaceKnowledgeBase,
  type WorkspaceKnowledgeDocument,
  type WorkspaceFileAnnotation,
  type WorkspaceFileAnnotationReply,
  type WorkspaceTeamMessage,
  type WorkspaceTeamDetail,
  type WorkspaceTeamInvite,
  type WorkspaceTeamMember,
  type WorkspaceWorkflow,
  type WorkspaceWorkflowExecution,
  type WorkspaceWorkflowValidation,
} from '@/client/workspace'
import { useWorkspaceStore } from '@/stores/workspace'

function getDemoFile(fileId: string) {
  const file = demoWorkspaceSnapshot.files.find((item) => item.id === fileId)
  if (!file) {
    throw new Error(`Missing demo file fixture: ${fileId}`)
  }
  return file
}

describe('workspace store file actions', () => {
  beforeEach(() => {
    window.localStorage.clear()
    setActivePinia(createPinia())
    vi.restoreAllMocks()
  })

  it('downloads a file through the generated-client adapter with the stored access token', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const fileBlob = new Blob(['file-content'], { type: 'application/octet-stream' })
    const downloadSpy = vi.spyOn(workspaceClient, 'downloadWorkspaceFile').mockResolvedValue(fileBlob)
    const workspace = useWorkspaceStore()

    const result = await workspace.downloadFile('file-microscope')

    expect(downloadSpy).toHaveBeenCalledWith('access-token', 'file-microscope')
    expect(result).toBe(fileBlob)
    expect(workspace.downloadingFileId).toBeNull()
  })

  it('creates a share link through the generated-client adapter with the stored access token', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const shareLink = {
      id: 'share-1',
      file_id: 'file-microscope',
      token: 'share-token',
      url: '/api/v1/share-links/share-token/download',
      expires_at: '2026-07-09T11:00:00+08:00',
      download_limit: 3,
      download_count: 0,
      has_password: true,
    }
    const shareSpy = vi.spyOn(workspaceClient, 'createWorkspaceFileShareLink').mockResolvedValue(shareLink)
    const workspace = useWorkspaceStore()

    const result = await workspace.createFileShareLink('file-microscope', {
      downloadLimit: 3,
      expiresInSeconds: 900,
      password: 'view-pass',
    })

    expect(shareSpy).toHaveBeenCalledWith('access-token', 'file-microscope', {
      downloadLimit: 3,
      expiresInSeconds: 900,
      password: 'view-pass',
    })
    expect(result).toEqual(shareLink)
    expect(workspace.sharingFileId).toBeNull()
  })

  it('deletes a file through the generated-client adapter and removes it from the current snapshot', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const deleteSpy = vi.spyOn(workspaceClient, 'deleteWorkspaceFile').mockResolvedValue()
    const workspace = useWorkspaceStore()

    await workspace.deleteFile('file-microscope')

    expect(deleteSpy).toHaveBeenCalledWith('access-token', 'file-microscope')
    expect(workspace.files.some((file) => file.id === 'file-microscope')).toBe(false)
    expect(workspace.deletingFileId).toBeNull()
  })

  it('loads recycle-bin files and restores a soft-deleted file through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const deletedFile = getDemoFile('file-microscope')
    const recycledItem = {
      deleted_at: '2026-07-09T18:20:00+08:00',
      deleted_by: 'xiaoming',
      file: deletedFile,
    }
    vi.spyOn(workspaceClient, 'deleteWorkspaceFile').mockResolvedValue()
    const listRecycleBinSpy = vi.spyOn(workspaceClient, 'listWorkspaceRecycleBin').mockResolvedValue({
      items: [recycledItem],
      total: 1,
    })
    const restoreSpy = vi.spyOn(workspaceClient, 'restoreWorkspaceDeletedFile').mockResolvedValue(deletedFile)
    const workspace = useWorkspaceStore()

    await workspace.deleteFile('file-microscope')
    await workspace.loadRecycleBin()
    await workspace.restoreDeletedFile('file-microscope')

    expect(listRecycleBinSpy).toHaveBeenCalledWith('access-token')
    expect(workspace.recycleBinItems).toEqual([])
    expect(restoreSpy).toHaveBeenCalledWith('access-token', 'file-microscope')
    expect(workspace.files[0]).toEqual(deletedFile)
    expect(workspace.summary.file_count).toBe(demoWorkspaceSnapshot.summary.file_count)
    expect(workspace.recycleBinLoading).toBe(false)
    expect(workspace.restoringDeletedFileId).toBeNull()
  })

  it('searches files through the generated-client adapter and stores active filters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const searchedFile = getDemoFile('file-microscope')
    const listSpy = vi.spyOn(workspaceClient, 'listWorkspaceFiles').mockResolvedValue({
      items: [searchedFile],
      total: 1,
    })
    const workspace = useWorkspaceStore()

    await workspace.searchFiles({
      fileType: 'pdf',
      query: '显微镜',
      tag: '实验',
      updatedFrom: '2026-07-08T00:00:00+08:00',
      updatedTo: '2026-07-09T00:00:00+08:00',
    })

    expect(listSpy).toHaveBeenCalledWith('access-token', {
      fileType: 'pdf',
      query: '显微镜',
      tag: '实验',
      updatedFrom: '2026-07-08T00:00:00+08:00',
      updatedTo: '2026-07-09T00:00:00+08:00',
    })
    expect(workspace.fileFilters).toEqual({
      fileType: 'pdf',
      query: '显微镜',
      tag: '实验',
      updatedFrom: '2026-07-08T00:00:00+08:00',
      updatedTo: '2026-07-09T00:00:00+08:00',
    })
    expect(workspace.files).toEqual([searchedFile])
    expect(workspace.fileListLoading).toBe(false)
  })

  it('uploads a file through the generated-client adapter and prepends it to the snapshot', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const uploadFile = new File(['细胞壁清晰可见。'], '观察记录.md', { type: 'text/markdown' })
    const uploaded = {
      ...getDemoFile('file-microscope'),
      id: 'file-uploaded',
      name: '观察记录.md',
      parse_status: 'queued' as const,
      tags: ['实验', '观察'],
      type: 'markdown',
    }
    const uploadSpy = vi.spyOn(workspaceClient, 'uploadWorkspaceFile').mockResolvedValue(uploaded)
    const workspace = useWorkspaceStore()

    await workspace.uploadFile({ file: uploadFile, folderId: 'personal-root', tags: ['实验', '观察'] })

    expect(uploadSpy).toHaveBeenCalledWith('access-token', {
      file: uploadFile,
      folderId: 'personal-root',
      tags: ['实验', '观察'],
    })
    expect(workspace.files[0]).toEqual(uploaded)
    expect(workspace.summary.file_count).toBe(demoWorkspaceSnapshot.summary.file_count + 1)
    expect(workspace.uploadingFile).toBe(false)
  })

  it('uploads a large file through the multipart adapter and prepends it to the snapshot', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const uploadFile = new File(['第一片', '第二片'], '大文件观察记录.md', { type: 'text/markdown' })
    const uploaded = {
      ...getDemoFile('file-microscope'),
      id: 'file-large-uploaded',
      name: '大文件观察记录.md',
      parse_status: 'queued' as const,
      tags: ['实验', '分片'],
      type: 'markdown',
    }
    const uploadSpy = vi.spyOn(workspaceClient, 'uploadWorkspaceMultipartFile').mockResolvedValue(uploaded)
    const workspace = useWorkspaceStore()

    await workspace.uploadLargeFile({
      chunkSize: 3,
      file: uploadFile,
      folderId: 'personal-root',
      tags: ['实验', '分片'],
    })

    expect(uploadSpy).toHaveBeenCalledWith('access-token', {
      chunkSize: 3,
      file: uploadFile,
      folderId: 'personal-root',
      tags: ['实验', '分片'],
    })
    expect(workspace.files[0]).toEqual(uploaded)
    expect(workspace.summary.file_count).toBe(demoWorkspaceSnapshot.summary.file_count + 1)
    expect(workspace.uploadingFile).toBe(false)
  })

  it('updates file metadata through the generated-client adapter and replaces the snapshot row', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const updated = {
      ...getDemoFile('file-microscope'),
      name: '显微镜实验归档.pdf',
      folder_id: 'folder-course',
      tags: ['实验', '归档'],
    }
    const updateSpy = vi.spyOn(workspaceClient, 'updateWorkspaceFile').mockResolvedValue(updated)
    const workspace = useWorkspaceStore()

    await workspace.updateFile('file-microscope', {
      folderId: 'folder-course',
      name: '显微镜实验归档.pdf',
      tags: ['实验', '归档'],
    })

    expect(updateSpy).toHaveBeenCalledWith('access-token', 'file-microscope', {
      folderId: 'folder-course',
      name: '显微镜实验归档.pdf',
      tags: ['实验', '归档'],
    })
    expect(workspace.files.find((file) => file.id === 'file-microscope')).toEqual(updated)
    expect(workspace.updatingFileId).toBeNull()
  })

  it('copies a file through the generated-client adapter and prepends the copied file', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const copied = {
      ...getDemoFile('file-microscope'),
      id: 'file-copy',
      name: '显微镜实验报告 副本.pdf',
      folder_id: 'folder-course',
    }
    const copySpy = vi.spyOn(workspaceClient, 'copyWorkspaceFile').mockResolvedValue(copied)
    const workspace = useWorkspaceStore()

    await workspace.copyFile('file-microscope', {
      name: '显微镜实验报告 副本.pdf',
      targetFolderId: 'folder-course',
    })

    expect(copySpy).toHaveBeenCalledWith('access-token', 'file-microscope', {
      name: '显微镜实验报告 副本.pdf',
      targetFolderId: 'folder-course',
    })
    expect(workspace.files[0]).toEqual(copied)
    expect(workspace.summary.file_count).toBe(demoWorkspaceSnapshot.summary.file_count + 1)
    expect(workspace.copyingFileId).toBeNull()
  })

  it('loads file versions and restores a selected version through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const versions: WorkspaceFileVersion[] = [
      createVersion('version-2', 2, true),
      createVersion('version-1', 1, false),
    ]
    const restored = {
      ...getDemoFile('file-microscope'),
      sha256: 'restored-sha256',
      parse_status: 'queued' as const,
    }
    const listSpy = vi.spyOn(workspaceClient, 'listWorkspaceFileVersions').mockResolvedValue({ items: versions })
    const restoreSpy = vi.spyOn(workspaceClient, 'restoreWorkspaceFileVersion').mockResolvedValue(restored)
    const workspace = useWorkspaceStore()

    await workspace.loadFileVersions('file-microscope')
    await workspace.restoreFileVersion('file-microscope', 'version-1')

    expect(listSpy).toHaveBeenCalledWith('access-token', 'file-microscope')
    expect(workspace.fileVersionsById['file-microscope']).toEqual(versions)
    expect(restoreSpy).toHaveBeenCalledWith('access-token', 'file-microscope', 'version-1')
    expect(workspace.files.find((file) => file.id === 'file-microscope')).toEqual(restored)
    expect(workspace.versionFileId).toBeNull()
    expect(workspace.restoringVersionId).toBeNull()
  })

  it('loads the folder tree through the generated-client adapter with the stored access token', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const folderTree = createFolderTree()
    const listSpy = vi.spyOn(workspaceClient, 'listWorkspaceFolders').mockResolvedValue({ items: folderTree })
    const workspace = useWorkspaceStore()

    await workspace.loadFolders()

    expect(listSpy).toHaveBeenCalledWith('access-token')
    expect(workspace.folders).toEqual(folderTree)
    expect(workspace.activeFolderId).toBe('personal-root')
    expect(workspace.folderOptions).toEqual([
      { label: '个人文件', value: 'personal-root' },
      { label: '个人文件 / 生物学实验', value: 'folder-biology' },
      { label: '个人文件 / 软件工程课程', value: 'folder-course' },
      { label: '团队文件', value: 'team-root' },
    ])
  })

  it('creates a folder and inserts it under the selected parent', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    vi.spyOn(workspaceClient, 'listWorkspaceFolders').mockResolvedValue({ items: createFolderTree() })
    const createdFolder: WorkspaceFolder = {
      id: 'folder-notes',
      name: '观察记录',
      parent_id: 'personal-root',
      permission: '个人',
      scope: 'personal',
      children: [],
    }
    const createSpy = vi.spyOn(workspaceClient, 'createWorkspaceFolder').mockResolvedValue(createdFolder)
    const workspace = useWorkspaceStore()
    await workspace.loadFolders()

    await workspace.createFolder({ name: '观察记录', parentId: 'personal-root', scope: 'personal' })

    expect(createSpy).toHaveBeenCalledWith('access-token', {
      name: '观察记录',
      parentId: 'personal-root',
      scope: 'personal',
    })
    expect(workspace.folderOptions.map((option) => option.value)).toContain('folder-notes')
    expect(workspace.creatingFolder).toBe(false)
  })

  it('renames and moves a folder within the stored tree', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    vi.spyOn(workspaceClient, 'listWorkspaceFolders').mockResolvedValue({ items: createFolderTree() })
    const movedFolder: WorkspaceFolder = {
      id: 'folder-biology',
      name: '实验归档',
      parent_id: 'folder-course',
      permission: '个人',
      scope: 'personal',
      children: [],
    }
    const updateSpy = vi.spyOn(workspaceClient, 'updateWorkspaceFolder').mockResolvedValue(movedFolder)
    const workspace = useWorkspaceStore()
    await workspace.loadFolders()

    await workspace.updateFolder('folder-biology', { name: '实验归档', parentId: 'folder-course' })

    expect(updateSpy).toHaveBeenCalledWith('access-token', 'folder-biology', {
      name: '实验归档',
      parentId: 'folder-course',
    })
    expect(workspace.folderOptions).toContainEqual({
      label: '个人文件 / 软件工程课程 / 实验归档',
      value: 'folder-biology',
    })
    expect(workspace.folderOptions).not.toContainEqual({
      label: '个人文件 / 生物学实验',
      value: 'folder-biology',
    })
    expect(workspace.updatingFolderId).toBeNull()
  })

  it('deletes a folder from the stored tree and clears active selection when needed', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    vi.spyOn(workspaceClient, 'listWorkspaceFolders').mockResolvedValue({ items: createFolderTree() })
    const deleteSpy = vi.spyOn(workspaceClient, 'deleteWorkspaceFolder').mockResolvedValue()
    const workspace = useWorkspaceStore()
    await workspace.loadFolders()
    workspace.selectFolder('folder-biology')

    await workspace.deleteFolder('folder-biology')

    expect(deleteSpy).toHaveBeenCalledWith('access-token', 'folder-biology')
    expect(workspace.folderOptions.map((option) => option.value)).not.toContain('folder-biology')
    expect(workspace.activeFolderId).toBe('personal-root')
    expect(workspace.deletingFolderId).toBeNull()
  })

  it('manages team detail, invites, roles, and removals through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const createdTeam = createTeamDetail()
    const invitedMember = createTeamMember('member-2', 'member')
    const invite: WorkspaceTeamInvite = {
      created_at: '2026-07-08T08:00:00+08:00',
      email: 'xiaohong@example.com',
      expires_at: '2026-07-15T08:00:00+08:00',
      id: 'invite-1',
      role: 'member',
      status: 'pending',
      team_id: 'team-algo',
      token: 'invite-token',
    }
    const updatedMember = { ...invitedMember, role: 'admin' as const }
    const createSpy = vi.spyOn(workspaceClient, 'createWorkspaceTeam').mockResolvedValue(createdTeam)
    const detailSpy = vi.spyOn(workspaceClient, 'loadWorkspaceTeamDetail').mockResolvedValue(createdTeam)
    const inviteSpy = vi.spyOn(workspaceClient, 'createWorkspaceTeamInvite').mockResolvedValue(invite)
    const updateMemberSpy = vi.spyOn(workspaceClient, 'updateWorkspaceTeamMember').mockResolvedValue(updatedMember)
    const removeMemberSpy = vi.spyOn(workspaceClient, 'removeWorkspaceTeamMember').mockResolvedValue()
    const workspace = useWorkspaceStore()

    await workspace.createTeam({ name: ' 算法课程小组 ', description: ' 课程资料协作 ' })
    await workspace.loadTeamDetail('team-algo')
    await workspace.inviteTeamMember('team-algo', { email: 'xiaohong@example.com', role: 'member' })
    await workspace.updateTeamMemberRole('team-algo', 'member-2', 'admin')
    await workspace.removeTeamMember('team-algo', 'member-2')

    expect(createSpy).toHaveBeenCalledWith('access-token', {
      description: '课程资料协作',
      name: '算法课程小组',
    })
    expect(detailSpy).toHaveBeenCalledWith('access-token', 'team-algo')
    expect(inviteSpy).toHaveBeenCalledWith('access-token', 'team-algo', {
      email: 'xiaohong@example.com',
      role: 'member',
    })
    expect(updateMemberSpy).toHaveBeenCalledWith('access-token', 'team-algo', 'member-2', 'admin')
    expect(removeMemberSpy).toHaveBeenCalledWith('access-token', 'team-algo', 'member-2')
    expect(workspace.teams[0]).toMatchObject({ id: 'team-algo', member_count: 1 })
    expect(workspace.activeTeamDetail?.invites).toEqual([invite])
    expect(workspace.activeTeamDetail?.members.map((member) => member.id)).not.toContain('member-2')
    expect(workspace.teamOperationLoading).toBe(false)
  })

  it('loads and sends team messages through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const historyMessage = createTeamMessage('msg-1', 'xiaohong', '已上传实验记录。')
    const sentMessage = createTeamMessage('msg-2', 'xiaoming', '请 @xiaohong 看一下实验记录。')
    const listSpy = vi.spyOn(workspaceClient, 'listWorkspaceTeamMessages').mockResolvedValue({
      items: [historyMessage],
      total: 1,
    })
    const sendSpy = vi.spyOn(workspaceClient, 'sendWorkspaceTeamMessage').mockResolvedValue(sentMessage)
    const workspace = useWorkspaceStore()

    await workspace.loadTeamMessages('team-algo')
    await workspace.sendTeamMessage('team-algo', { content: ' 请 @xiaohong 看一下实验记录。 ' })

    expect(listSpy).toHaveBeenCalledWith('access-token', 'team-algo')
    expect(sendSpy).toHaveBeenCalledWith('access-token', 'team-algo', {
      content: '请 @xiaohong 看一下实验记录。',
      message_type: 'text',
      receiver_id: null,
    })
    expect(workspace.teamMessagesById['team-algo']).toEqual([historyMessage, sentMessage])
    expect(workspace.teamMessageTeamIdLoading).toBeNull()
    expect(workspace.teamMessageSending).toBe(false)
  })

  it('manages knowledge bases, indexed documents, and RAG questions through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const knowledgeBase = createKnowledgeBase()
    const createdKnowledgeBase = {
      ...knowledgeBase,
      description: '课程实验检索',
      document_count: 0,
    }
    const document = createKnowledgeDocument()
    const qaResponse = {
      answer: '归并排序先递归拆分序列，再合并有序子序列，时间复杂度为 O(n log n)。',
      citations: [
        {
          chunk_id: 'chunk-sort-1',
          document_id: 'doc-kb-algo-file-microscope',
          file_id: 'file-microscope',
          page_no: 1,
          paragraph_no: 1,
          snippet: '归并排序先递归拆分序列，再合并有序子序列，时间复杂度为 O(n log n)。',
          title: '显微镜实验报告.pdf',
        },
      ],
      conversation_id: 'conv-sort',
      message_id: 'msg-sort',
    }
    const listSpy = vi.spyOn(workspaceClient, 'listKnowledgeBases').mockResolvedValue({ items: [knowledgeBase] })
    const createSpy = vi.spyOn(workspaceClient, 'createKnowledgeBase').mockResolvedValue(createdKnowledgeBase)
    const listDocsSpy = vi.spyOn(workspaceClient, 'listKnowledgeDocuments').mockResolvedValue({ items: [document] })
    const addDocSpy = vi.spyOn(workspaceClient, 'addKnowledgeDocument').mockResolvedValue(document)
    const askSpy = vi.spyOn(workspaceClient, 'askWorkspaceQuestion').mockResolvedValue(qaResponse)
    const workspace = useWorkspaceStore()

    await workspace.loadKnowledgeBases()
    await workspace.createKnowledgeBase({ description: ' 课程实验检索 ', name: ' 算法实验知识库 ' })
    await workspace.loadKnowledgeDocuments('kb-algo')
    await workspace.addKnowledgeDocument('kb-algo', 'file-microscope')
    await workspace.askKnowledgeQuestion({
      kbId: 'kb-algo',
      question: ' 归并排序的步骤和复杂度是什么？ ',
      topK: 2,
    })

    expect(listSpy).toHaveBeenCalledWith('access-token')
    expect(createSpy).toHaveBeenCalledWith('access-token', {
      description: '课程实验检索',
      name: '算法实验知识库',
    })
    expect(listDocsSpy).toHaveBeenCalledWith('access-token', 'kb-algo')
    expect(addDocSpy).toHaveBeenCalledWith('access-token', 'kb-algo', 'file-microscope')
    expect(askSpy).toHaveBeenCalledWith('access-token', {
      conversationId: null,
      kbId: 'kb-algo',
      question: '归并排序的步骤和复杂度是什么？',
      topK: 2,
    })
    expect(workspace.knowledgeBases[0]).toEqual({
      ...createdKnowledgeBase,
      chunk_count: document.chunk_count,
      document_count: 1,
      updated_at: document.updated_at,
    })
    expect(workspace.activeKnowledgeBaseId).toBe('kb-algo')
    expect(workspace.activeKnowledgeDocuments).toEqual([document])
    expect(workspace.narrative.answer).toContain('归并排序')
    const firstCitation = workspace.narrative.citations[0]
    expect(firstCitation).toBeDefined()
    expect(firstCitation?.file_id).toBe('file-microscope')
    expect(workspace.askingQuestion).toBe(false)
    expect(workspace.knowledgeOperationLoading).toBe(false)
  })

  it('manages workflow definitions, validation, publication, and execution through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const createdWorkflow = createWorkflowDefinition('workflow-weekly', 'draft')
    const updatedWorkflow = {
      ...createdWorkflow,
      description: '从团队目录检索进展并生成 Markdown 周报',
      node_count: 4,
      nodes: [
        ...(createdWorkflow.nodes ?? []),
        {
          id: 'output',
          name: '输出 Markdown',
          parameters: { target: 'workspace' },
          type: 'output' as const,
        },
      ],
      edges: [
        ...(createdWorkflow.edges ?? []),
        { id: 'edge-report-output', source: 'report', target: 'output' },
      ],
    }
    const validation: WorkspaceWorkflowValidation = {
      edge_count: 3,
      issues: [],
      node_count: 4,
      valid: true,
    }
    const publishedWorkflow = { ...updatedWorkflow, status: 'published' as const, version: '1.0.0' }
    const execution: WorkspaceWorkflowExecution = {
      id: 'exec-weekly',
      node_executions: [
        {
          input: { file_id: 'file-weekly' },
          name: '选择团队文件',
          node_id: 'input',
          output: { accepted: true },
          status: 'success',
          tool_name: 'trigger',
        },
        {
          input: { file_id: 'file-weekly' },
          name: '生成周报',
          node_id: 'report',
          output: { format: 'markdown' },
          status: 'success',
          tool_name: 'report_generate',
        },
      ],
      output: { summary: '团队周报生成 已完成：基于 小组周报.docx 生成流程输出。' },
      status: 'completed',
      workflow_id: 'workflow-weekly',
    }
    const createSpy = vi.spyOn(workspaceClient, 'createWorkspaceWorkflow').mockResolvedValue(createdWorkflow)
    const updateSpy = vi.spyOn(workspaceClient, 'updateWorkspaceWorkflow').mockResolvedValue(updatedWorkflow)
    const validateSpy = vi.spyOn(workspaceClient, 'validateWorkspaceWorkflow').mockResolvedValue(validation)
    const publishSpy = vi.spyOn(workspaceClient, 'publishWorkspaceWorkflow').mockResolvedValue(publishedWorkflow)
    const executeSpy = vi.spyOn(workspaceClient, 'executeWorkspaceWorkflow').mockResolvedValue(execution)
    const workspace = useWorkspaceStore()

    await workspace.createWorkflow({
      description: ' 汇总团队文件并生成 Markdown 周报 ',
      edges: createdWorkflow.edges ?? [],
      name: ' 团队周报生成 ',
      nodes: createdWorkflow.nodes ?? [],
      trigger: 'manual',
    })
    await workspace.updateWorkflow('workflow-weekly', {
      description: ' 从团队目录检索进展并生成 Markdown 周报 ',
      edges: updatedWorkflow.edges ?? [],
      nodes: updatedWorkflow.nodes ?? [],
    })
    await workspace.validateWorkflow('workflow-weekly')
    await workspace.publishWorkflow('workflow-weekly')
    await workspace.executeWorkflow('workflow-weekly', { fileId: 'file-weekly', targetKbId: 'kb-course' })

    expect(createSpy).toHaveBeenCalledWith('access-token', {
      description: '汇总团队文件并生成 Markdown 周报',
      edges: createdWorkflow.edges,
      name: '团队周报生成',
      nodes: createdWorkflow.nodes,
      trigger: 'manual',
    })
    expect(updateSpy).toHaveBeenCalledWith('access-token', 'workflow-weekly', {
      description: '从团队目录检索进展并生成 Markdown 周报',
      edges: updatedWorkflow.edges,
      nodes: updatedWorkflow.nodes,
    })
    expect(validateSpy).toHaveBeenCalledWith('access-token', 'workflow-weekly')
    expect(publishSpy).toHaveBeenCalledWith('access-token', 'workflow-weekly')
    expect(executeSpy).toHaveBeenCalledWith('access-token', 'workflow-weekly', {
      fileId: 'file-weekly',
      targetKbId: 'kb-course',
    })
    expect(workspace.activeWorkflowId).toBe('workflow-weekly')
    expect(workspace.activeWorkflowValidation).toEqual(validation)
    expect(workspace.activeWorkflowExecution).toEqual(execution)
    expect(workspace.workflows[0]).toEqual(publishedWorkflow)
    expect(workspace.narrative.agentSteps.map((step) => step.tool_name)).toContain('report_generate')
    expect(workspace.workflowOperationLoading).toBe(false)
  })

  it('manages permission rules through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const inheritedDeny = createPermissionRule('rule-folder-deny', {
      action: 'read',
      effect: 'deny',
      inherit: true,
      resource_id: 'team-root',
      resource_label: '团队文件',
      resource_type: 'folder',
      subject_id: 'team-biology:guest',
      subject_label: '生物学实验 / 访客',
      subject_type: 'role',
    })
    const directOverride = createPermissionRule('rule-file-allow', {
      action: 'write',
      effect: 'allow',
      inherit: false,
      resource_id: 'file-weekly',
      resource_label: '小组周报.docx',
      resource_type: 'file',
      subject_id: 'team-biology:member',
      subject_label: '生物学实验 / 成员',
      subject_type: 'role',
    })
    const listSpy = vi.spyOn(workspaceClient, 'listWorkspacePermissionRules').mockResolvedValue({
      items: [inheritedDeny],
    })
    const createSpy = vi.spyOn(workspaceClient, 'createWorkspacePermissionRule').mockResolvedValue(directOverride)
    const deleteSpy = vi.spyOn(workspaceClient, 'deleteWorkspacePermissionRule').mockResolvedValue()
    const workspace = useWorkspaceStore()

    await workspace.loadPermissionRules()
    await workspace.createPermissionRule({
      action: 'write',
      effect: 'allow',
      inherit: false,
      resourceId: 'file-weekly',
      resourceType: 'file',
      subjectId: 'team-biology:member',
      subjectType: 'role',
    })
    await workspace.deletePermissionRule('rule-folder-deny')

    expect(listSpy).toHaveBeenCalledWith('access-token')
    expect(createSpy).toHaveBeenCalledWith('access-token', {
      action: 'write',
      effect: 'allow',
      inherit: false,
      resourceId: 'file-weekly',
      resourceType: 'file',
      subjectId: 'team-biology:member',
      subjectType: 'role',
    })
    expect(deleteSpy).toHaveBeenCalledWith('access-token', 'rule-folder-deny')
    expect(workspace.permissionRules).toEqual([directOverride])
    expect(workspace.permissionRulesLoading).toBe(false)
    expect(workspace.permissionRuleSaving).toBe(false)
    expect(workspace.deletingPermissionRuleId).toBeNull()
  })

  it('manages file annotations and replies through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const annotation = createAnnotation('anno-1', 'file-weekly', '需要补充数据来源')
    const createdAnnotation = createAnnotation('anno-2', 'file-weekly', '请确认图表单位')
    const reply = createReply('reply-1', 'anno-1', 'file-weekly', '已补充')
    const listSpy = vi.spyOn(workspaceClient, 'listWorkspaceFileAnnotations').mockResolvedValue({
      items: [annotation],
      total: 1,
    })
    const createSpy = vi.spyOn(workspaceClient, 'createWorkspaceFileAnnotation').mockResolvedValue(createdAnnotation)
    const replySpy = vi.spyOn(workspaceClient, 'replyWorkspaceFileAnnotation').mockResolvedValue(reply)
    const deleteSpy = vi.spyOn(workspaceClient, 'deleteWorkspaceFileAnnotation').mockResolvedValue()
    const workspace = useWorkspaceStore()

    await workspace.loadFileAnnotations('file-weekly')
    await workspace.createFileAnnotation('file-weekly', {
      content: ' 请确认图表单位 ',
      position: { page: 3 },
    })
    await workspace.replyFileAnnotation('anno-1', { content: ' 已补充 ' })
    await workspace.deleteFileAnnotation('file-weekly', 'reply-1')

    expect(listSpy).toHaveBeenCalledWith('access-token', 'file-weekly')
    expect(createSpy).toHaveBeenCalledWith('access-token', 'file-weekly', {
      content: '请确认图表单位',
      position: { page: 3 },
    })
    expect(replySpy).toHaveBeenCalledWith('access-token', 'anno-1', { content: '已补充' })
    expect(deleteSpy).toHaveBeenCalledWith('access-token', 'file-weekly', 'reply-1')
    expect(workspace.fileAnnotationsById['file-weekly']).toEqual([createdAnnotation, annotation])
    expect(workspace.annotationFileIdLoading).toBeNull()
    expect(workspace.annotationSaving).toBe(false)
    expect(workspace.deletingAnnotationId).toBeNull()
  })

  it('loads notifications and marks a notification read through generated-client adapters', async () => {
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '小明',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const unreadNotification = createNotification('noti-1', {
      content: '李老师回复了 小组周报.docx 的批注',
      is_read: false,
      title: '批注收到回复',
      type: 'annotation',
    })
    const readNotification = createNotification('noti-2', {
      content: '王老师邀请你加入算法课程小组',
      is_read: true,
      title: '团队邀请',
      type: 'invite',
    })
    const markedNotification = { ...unreadNotification, is_read: true }
    const listSpy = vi.spyOn(workspaceClient, 'listWorkspaceNotifications').mockResolvedValue({
      items: [unreadNotification, readNotification],
      total: 2,
      unread_count: 1,
    })
    const markSpy = vi.spyOn(workspaceClient, 'markWorkspaceNotificationRead').mockResolvedValue(markedNotification)
    const workspace = useWorkspaceStore()

    await workspace.loadNotifications()
    await workspace.markNotificationRead('noti-1')

    expect(listSpy).toHaveBeenCalledWith('access-token')
    expect(markSpy).toHaveBeenCalledWith('access-token', 'noti-1')
    expect(workspace.notifications).toEqual([markedNotification, readNotification])
    expect(workspace.summary.unread_notifications).toBe(0)
    expect(workspace.notificationsLoading).toBe(false)
    expect(workspace.markingNotificationId).toBeNull()
  })
})

function createFolderTree(): WorkspaceFolder[] {
  return [
    {
      id: 'personal-root',
      name: '个人文件',
      parent_id: null,
      permission: '个人',
      scope: 'personal',
      children: [
        {
          id: 'folder-biology',
          name: '生物学实验',
          parent_id: 'personal-root',
          permission: '个人',
          scope: 'personal',
          children: [],
        },
        {
          id: 'folder-course',
          name: '软件工程课程',
          parent_id: 'personal-root',
          permission: '个人',
          scope: 'personal',
          children: [],
        },
      ],
    },
    {
      id: 'team-root',
      name: '团队文件',
      parent_id: null,
      permission: '团队',
      scope: 'team',
      children: [],
    },
  ]
}

function createVersion(id: string, versionNo: number, isCurrent: boolean): WorkspaceFileVersion {
  return {
    created_at: '2026-07-08T08:00:00+08:00',
    created_by: 'xiaoming',
    file_id: 'file-microscope',
    id,
    is_current: isCurrent,
    name: '显微镜实验报告.pdf',
    sha256: `sha-${versionNo}`,
    size: 1024 + versionNo,
    version_no: versionNo,
  }
}

function createAnnotation(id: string, fileId: string, content: string): WorkspaceFileAnnotation {
  return {
    author_id: 1,
    author_name: 'xiaoming',
    content,
    created_at: '2026-07-09T08:00:00+08:00',
    file_id: fileId,
    id,
    position: null,
    replies: [],
    updated_at: '2026-07-09T08:00:00+08:00',
  }
}

function createReply(id: string, annotationId: string, fileId: string, content: string): WorkspaceFileAnnotationReply {
  return {
    annotation_id: annotationId,
    author_id: 2,
    author_name: 'team-owner',
    content,
    created_at: '2026-07-09T08:10:00+08:00',
    file_id: fileId,
    id,
    updated_at: '2026-07-09T08:10:00+08:00',
  }
}

function createNotification(id: string, overrides: Partial<WorkspaceNotification>): WorkspaceNotification {
  return {
    content: null,
    created_at: '2026-07-09T12:00:00Z',
    id,
    is_read: false,
    target_id: 'file-weekly',
    target_type: 'file',
    title: '通知',
    type: 'system',
    user_id: 1,
    ...overrides,
  }
}

function createPermissionRule(
  id: string,
  overrides: Omit<WorkspacePermissionRule, 'created_at' | 'created_by' | 'id'>,
): WorkspacePermissionRule {
  return {
    created_at: '2026-07-08T08:00:00+08:00',
    created_by: 'xiaoming',
    id,
    ...overrides,
  }
}

function createTeamDetail(): WorkspaceTeamDetail {
  return {
    description: '课程资料协作',
    id: 'team-algo',
    invites: [],
    member_count: 2,
    members: [createTeamMember('member-1', 'owner'), createTeamMember('member-2', 'member')],
    name: '算法课程小组',
    role: 'owner',
    root_folder: {
      children: [],
      id: 'team-algo-root',
      name: '算法课程小组',
      parent_id: null,
      permission: '管理',
      scope: 'team',
      team_id: 'team-algo',
    },
    unread_count: 0,
  }
}

function createTeamMember(id: string, role: WorkspaceTeamMember['role']): WorkspaceTeamMember {
  return {
    display_name: id === 'member-1' ? '小明' : '小红',
    email: id === 'member-1' ? 'xiaoming@example.com' : 'xiaohong@example.com',
    id,
    joined_at: '2026-07-08T08:00:00+08:00',
    role,
    status: 'active',
    team_id: 'team-algo',
    user_id: id === 'member-1' ? 1 : 2,
    username: id === 'member-1' ? 'xiaoming' : 'xiaohong',
  }
}

function createTeamMessage(id: string, senderName: string, content: string): WorkspaceTeamMessage {
  return {
    content,
    created_at: '2026-07-09T08:00:00+08:00',
    id,
    message_type: 'text',
    receiver_id: null,
    sender_id: senderName === 'xiaoming' ? 1 : 2,
    sender_name: senderName,
    team_id: 'team-algo',
  }
}

function createKnowledgeBase(): WorkspaceKnowledgeBase {
  return {
    chunk_count: 1,
    description: '算法课程实验记录',
    document_count: 1,
    id: 'kb-algo',
    name: '算法实验知识库',
    status: 'active',
    updated_at: '2026-07-08T08:00:00+08:00',
  }
}

function createKnowledgeDocument(): WorkspaceKnowledgeDocument {
  return {
    chunk_count: 1,
    file_id: 'file-microscope',
    file_name: '显微镜实验报告.pdf',
    id: 'doc-kb-algo-file-microscope',
    index_status: 'indexed',
    kb_id: 'kb-algo',
    updated_at: '2026-07-08T08:05:00+08:00',
  }
}

function createWorkflowDefinition(id: string, status: WorkspaceWorkflow['status']): WorkspaceWorkflow {
  return {
    description: '汇总团队文件并生成 Markdown 周报',
    edges: [
      { id: 'edge-input-search', source: 'input', target: 'search' },
      { id: 'edge-search-report', source: 'search', target: 'report' },
    ],
    id,
    name: '团队周报生成',
    node_count: 3,
    nodes: [
      {
        id: 'input',
        name: '选择团队文件',
        parameters: { source: 'team-folder' },
        type: 'trigger',
      },
      {
        id: 'search',
        name: '检索文件',
        parameters: { query: '周报' },
        tool_name: 'file_search',
        type: 'tool',
      },
      {
        id: 'report',
        name: '生成周报',
        parameters: { format: 'markdown' },
        tool_name: 'report_generate',
        type: 'tool',
      },
    ],
    status,
    trigger: 'manual',
    version: '0.1.0',
  }
}
