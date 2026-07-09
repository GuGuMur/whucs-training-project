import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { saveWorkspaceSession } from '@/auth'
import * as workspaceClient from '@/client/workspace'
import {
  demoWorkspaceSnapshot,
  type WorkspaceFileVersion,
  type WorkspaceFolder,
  type WorkspaceTeamDetail,
  type WorkspaceTeamInvite,
  type WorkspaceTeamMember,
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

    await workspace.searchFiles({ fileType: 'pdf', query: '显微镜', tag: '实验' })

    expect(listSpy).toHaveBeenCalledWith('access-token', {
      fileType: 'pdf',
      query: '显微镜',
      tag: '实验',
    })
    expect(workspace.fileFilters).toEqual({ fileType: 'pdf', query: '显微镜', tag: '实验' })
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
