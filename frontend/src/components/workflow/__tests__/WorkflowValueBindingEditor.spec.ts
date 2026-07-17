import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { defineComponent } from 'vue'

import WorkflowValueBindingEditor from '@/components/workflow/WorkflowValueBindingEditor.vue'

const stubs = {
  NInput: defineComponent({
    emits: ['update:value'],
    name: 'NInput',
    props: ['value'],
    template: '<input v-bind="$attrs" :value="value" @input="$emit(\'update:value\', $event.target.value)" />',
  }),
  NSelect: defineComponent({
    emits: ['update:value'],
    name: 'NSelect',
    props: ['options', 'value'],
    template: '<select v-bind="$attrs" :value="value" @change="$emit(\'update:value\', $event.target.value)"><option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option></select>',
  }),
}

describe('WorkflowValueBindingEditor', () => {
  it('emits literal binding updates', async () => {
    const wrapper = mount(WorkflowValueBindingEditor, {
      global: { stubs },
      props: {
        label: 'query',
        modelValue: { mode: 'literal', value: '' },
      },
    })

    await wrapper.find('[data-testid="binding-literal"]').setValue('machine learning')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([
      { mode: 'literal', value: 'machine learning' },
    ])
  })

  it('switches to the first available input binding', async () => {
    const wrapper = mount(WorkflowValueBindingEditor, {
      global: { stubs },
      props: {
        availableInputs: [{ key: 'kb_id', kind: 'knowledge_base', label: '目标知识库' }],
        modelValue: { mode: 'literal', value: '' },
      },
    })

    await wrapper.find('[data-testid="binding-mode"]').setValue('input')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([
      { inputKey: 'kb_id', mode: 'input' },
    ])
  })

  it('preserves number schema literals as numbers', async () => {
    const wrapper = mount(WorkflowValueBindingEditor, {
      global: { stubs },
      props: {
        modelValue: { mode: 'literal', value: 0 },
        schemaType: 'number',
      },
    })

    await wrapper.find('[data-testid="binding-literal"]').setValue('42.5')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([
      { mode: 'literal', value: 42.5 },
    ])
  })

  it('switches to an upstream node output binding', async () => {
    const wrapper = mount(WorkflowValueBindingEditor, {
      global: { stubs },
      props: {
        availableNodeOutputs: [{ label: '兴趣关键词', nodeId: 'extract', path: 'interests' }],
        modelValue: { mode: 'literal', value: '' },
      },
    })

    await wrapper.find('[data-testid="binding-mode"]').setValue('node')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([
      { mode: 'node', nodeId: 'extract', path: 'interests' },
    ])
  })
})
