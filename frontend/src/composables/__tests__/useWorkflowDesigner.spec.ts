import { describe, expect, it, vi } from 'vitest'

import { useWorkflowDesigner } from '../useWorkflowDesigner'

describe('useWorkflowDesigner', () => {
  it('adds, connects, and removes graph nodes through typed actions', () => {
    vi.stubGlobal('crypto', { randomUUID: vi.fn().mockReturnValueOnce('input').mockReturnValueOnce('tool').mockReturnValueOnce('edge') })
    const designer = useWorkflowDesigner()

    designer.addInputNode()
    designer.addToolNode({
      name: 'calculator',
      description: '计算',
      input_schema: { type: 'object', properties: { expression: { type: 'string' } } },
      risk_level: 'low',
    } as any)

    expect(designer.connect({ source: 'input-input', target: 'tool-tool', sourceHandle: 'output', targetHandle: 'input' })).toBe(true)
    expect(designer.edges.value).toHaveLength(1)
    expect(designer.isDirty.value).toBe(true)

    designer.selectedNodeId.value = 'input-input'
    designer.removeSelection()

    expect(designer.nodes.value.map((node) => node.id)).toEqual(['tool-tool'])
    expect(designer.edges.value).toHaveLength(0)
    vi.unstubAllGlobals()
  })

  it('undoes and redoes graph mutations', () => {
    vi.stubGlobal('crypto', { randomUUID: vi.fn().mockReturnValueOnce('input').mockReturnValueOnce('output') })
    const designer = useWorkflowDesigner()
    designer.addInputNode()
    designer.addOutputNode()
    expect(designer.nodes.value).toHaveLength(2)

    designer.undo()
    expect(designer.nodes.value).toHaveLength(1)
    expect(designer.canRedo.value).toBe(true)

    designer.redo()
    expect(designer.nodes.value).toHaveLength(2)
    vi.unstubAllGlobals()
  })

  it('creates bounded advanced nodes and preserves condition handles', () => {
    vi.stubGlobal('crypto', { randomUUID: vi.fn().mockReturnValueOnce('condition').mockReturnValueOnce('loop').mockReturnValueOnce('edge') })
    const designer = useWorkflowDesigner()
    designer.addAdvancedNode('condition')
    designer.addAdvancedNode('loop')

    expect(designer.nodes.value[0]?.data.parameters.operator).toBe('truthy')
    expect(designer.nodes.value[1]?.data.parameters.max_iterations).toBe(100)
    expect(designer.connect({ source: 'condition-condition', target: 'loop-loop', sourceHandle: 'true', targetHandle: 'input' })).toBe(true)
    expect(designer.edges.value[0]?.sourceHandle).toBe('true')
    vi.unstubAllGlobals()
  })

  it('ignores Vue Flow runtime metadata and execution status in dirty tracking', () => {
    vi.stubGlobal('crypto', { randomUUID: vi.fn().mockReturnValue('input') })
    const designer = useWorkflowDesigner()
    designer.addInputNode()
    designer.markSaved()

    const node = designer.nodes.value[0]!
    designer.nodes.value = [{
      ...node,
      selected: true,
      dimensions: { width: 240, height: 96 },
      data: { ...node.data, status: 'success' },
    } as any]

    expect(designer.isDirty.value).toBe(false)

    designer.nodes.value = [{
      ...designer.nodes.value[0]!,
      data: { ...designer.nodes.value[0]!.data, label: '已修改输入' },
    }]
    expect(designer.isDirty.value).toBe(true)
    vi.unstubAllGlobals()
  })
})
