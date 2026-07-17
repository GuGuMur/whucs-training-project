import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import WorkflowCanvas from '../WorkflowCanvas.vue'

vi.mock('@vue-flow/core', () => ({
  VueFlow: defineComponent({ name: 'VueFlow', setup: (_, { slots }) => () => h('div', { class: 'vue-flow-stub' }, slots.default?.()) }),
  useVueFlow: () => ({ fitView: vi.fn(), project: ({ x, y }: { x: number; y: number }) => ({ x, y }) }),
}))
vi.mock('@vue-flow/background', () => ({ Background: defineComponent({ setup: () => () => h('div') }) }))
vi.mock('@vue-flow/controls', () => ({ Controls: defineComponent({ setup: () => () => h('div') }) }))
vi.mock('@vue-flow/minimap', () => ({ MiniMap: defineComponent({ setup: () => () => h('div') }) }))

describe('WorkflowCanvas', () => {
  function mountCanvas() {
    return mount(WorkflowCanvas, {
      props: { tools: [], nodes: [], edges: [], 'onUpdate:nodes': vi.fn(), 'onUpdate:edges': vi.fn() },
      global: { stubs: { WorkflowNodePalette: { template: '<input data-testid="palette-input" />' }, NButton: { template: '<button><slot /></button>' } } },
    })
  }

  it('emits deletion for Delete and Backspace within the canvas scope', async () => {
    const wrapper = mountCanvas()
    await wrapper.find('.workflow-canvas-shell').trigger('keydown', { key: 'Delete' })
    await wrapper.find('.workflow-canvas-shell').trigger('keydown', { key: 'Backspace' })
    expect(wrapper.emitted('deleteSelection')).toHaveLength(2)
  })

  it('does not delete while editing a form control', async () => {
    const wrapper = mountCanvas()
    await wrapper.get('[data-testid="palette-input"]').trigger('keydown', { key: 'Delete' })
    expect(wrapper.emitted('deleteSelection')).toBeUndefined()
  })
})
