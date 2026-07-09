import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import {
  demoWorkspaceSnapshot,
  type WorkspaceFileAnnotation,
  type WorkspaceFileVersion,
} from '@/client/workspace'
import FileWorkbench from '../FileWorkbench.vue'

describe('FileWorkbench', () => {
  it('emits file download and delete actions from visible row controls', async () => {
    const TestHost = defineComponent({
      setup: () => () =>
        h(NConfigProvider, null, {
          default: () => h(FileWorkbench, { files: demoWorkspaceSnapshot.files }),
        }),
    })
    const wrapper = mount(TestHost, { global: { plugins: [naive] } })
    const workbench = wrapper.getComponent(FileWorkbench)

    await wrapper.get('[data-testid="download-file-file-microscope"]').trigger('click')
    await wrapper.get('[data-testid="delete-file-file-microscope"]').trigger('click')

    expect(workbench.emitted('download-file')?.[0]?.[0]).toMatchObject({ id: 'file-microscope' })
    expect(workbench.emitted('delete-file')?.[0]?.[0]).toMatchObject({ id: 'file-microscope' })
  })

  it('emits search filters from the file toolbar', async () => {
    const TestHost = defineComponent({
      setup: () => () =>
        h(NConfigProvider, null, {
          default: () => h(FileWorkbench, { files: demoWorkspaceSnapshot.files }),
        }),
    })
    const wrapper = mount(TestHost, { global: { plugins: [naive] } })
    const workbench = wrapper.getComponent(FileWorkbench)

    await wrapper.get('input[placeholder="搜索文件名"]').setValue(' 显微镜 ')
    await wrapper.get('input[placeholder="更新时间起"]').setValue('2026-07-08T00:00:00+08:00')
    await wrapper.get('input[placeholder="更新时间止"]').setValue('2026-07-09T00:00:00+08:00')
    await wrapper.get('[data-testid="search-files"]').trigger('click')

    expect(workbench.emitted('search-files')?.[0]?.[0]).toEqual({
      fileType: '',
      query: '显微镜',
      tag: '',
      updatedFrom: '2026-07-08T00:00:00+08:00',
      updatedTo: '2026-07-09T00:00:00+08:00',
    })
  })

  it('emits an upload payload from the upload panel', async () => {
    const TestHost = defineComponent({
      setup: () => () =>
        h(NConfigProvider, null, {
          default: () => h(FileWorkbench, { files: demoWorkspaceSnapshot.files }),
        }),
    })
    const wrapper = mount(TestHost, { global: { plugins: [naive] } })
    const workbench = wrapper.getComponent(FileWorkbench)
    const file = new File(['细胞壁清晰可见。'], '观察记录.md', { type: 'text/markdown' })

    await wrapper.get('[data-testid="open-upload-panel"]').trigger('click')
    const input = wrapper.get<HTMLInputElement>('[data-testid="upload-file-input"]')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')
    await wrapper.get('input[placeholder="实验, 观察"]').setValue('实验, 观察')
    await wrapper.get('[data-testid="submit-upload-file"]').trigger('click')

    expect(workbench.emitted('upload-file')?.[0]?.[0]).toEqual({
      file,
      folderId: 'personal-root',
      tags: ['实验', '观察'],
    })
  })

  it('emits file update, copy, version load, and restore actions from the lifecycle panel', async () => {
    const versions: WorkspaceFileVersion[] = [
      {
        created_at: '2026-07-08T08:10:00+08:00',
        created_by: 'xiaoming',
        file_id: 'file-microscope',
        id: 'version-2',
        is_current: true,
        name: '显微镜实验报告.pdf',
        sha256: 'sha-2',
        size: 2048,
        version_no: 2,
      },
      {
        created_at: '2026-07-08T07:10:00+08:00',
        created_by: 'xiaoming',
        file_id: 'file-microscope',
        id: 'version-1',
        is_current: false,
        name: '显微镜实验报告.pdf',
        sha256: 'sha-1',
        size: 1024,
        version_no: 1,
      },
    ]
    const TestHost = defineComponent({
      setup: () => () =>
        h(NConfigProvider, null, {
          default: () =>
            h(FileWorkbench, {
              fileVersionsById: { 'file-microscope': versions },
              files: demoWorkspaceSnapshot.files,
              folderOptions: [
                { label: '个人文件', value: 'personal-root' },
                { label: '个人文件 / 生物学实验', value: 'folder-biology' },
                { label: '个人文件 / 软件工程课程', value: 'folder-course' },
              ],
            }),
        }),
    })
    const wrapper = mount(TestHost, { global: { plugins: [naive] } })
    const workbench = wrapper.getComponent(FileWorkbench)

    await wrapper.get('[data-testid="manage-file-file-microscope"]').trigger('click')
    await wrapper.get('input[placeholder="文件名"]').setValue(' 显微镜实验归档.pdf ')
    await wrapper.get('input[placeholder="标签，用逗号分隔"]').setValue('实验, 归档')
    await wrapper.get('[data-testid="submit-update-file"]').trigger('click')
    await wrapper.get('input[placeholder="副本文件名"]').setValue('显微镜实验归档 副本.pdf')
    await wrapper.get('[data-testid="submit-copy-file"]').trigger('click')
    await wrapper.get('[data-testid="restore-version-version-1"]').trigger('click')

    expect(workbench.emitted('load-file-versions')?.[0]).toEqual(['file-microscope'])
    expect(workbench.emitted('update-file')?.[0]).toEqual([
      'file-microscope',
      {
        folderId: 'folder-biology',
        name: '显微镜实验归档.pdf',
        tags: ['实验', '归档'],
      },
    ])
    expect(workbench.emitted('copy-file')?.[0]).toEqual([
      'file-microscope',
      {
        name: '显微镜实验归档 副本.pdf',
        targetFolderId: 'folder-biology',
      },
    ])
    expect(workbench.emitted('restore-file-version')?.[0]).toEqual(['file-microscope', 'version-1'])
  })

  it('opens the annotation panel and forwards annotation actions', async () => {
    const annotations: WorkspaceFileAnnotation[] = [
      {
        author_id: 2,
        author_name: 'team-owner',
        content: '补充团队周报结论',
        created_at: '2026-07-09T08:00:00+08:00',
        file_id: 'file-weekly',
        id: 'anno-1',
        position: null,
        replies: [],
        updated_at: '2026-07-09T08:00:00+08:00',
      },
    ]
    const TestHost = defineComponent({
      setup: () => () =>
        h(NConfigProvider, null, {
          default: () =>
            h(FileWorkbench, {
              fileAnnotationsById: { 'file-weekly': annotations },
              files: demoWorkspaceSnapshot.files,
            }),
        }),
    })
    const wrapper = mount(TestHost, { global: { plugins: [naive] } })
    const workbench = wrapper.getComponent(FileWorkbench)

    await wrapper.get('[data-testid="annotate-file-file-weekly"]').trigger('click')
    await wrapper.get('textarea[placeholder="添加文件批注"]').setValue(' 请确认周报日期 ')
    await wrapper.get('[data-testid="submit-file-annotation"]').trigger('click')

    expect(workbench.emitted('load-file-annotations')?.[0]).toEqual(['file-weekly'])
    expect(workbench.emitted('create-file-annotation')?.[0]).toEqual([
      'file-weekly',
      { content: '请确认周报日期', position: null },
    ])
  })
})
