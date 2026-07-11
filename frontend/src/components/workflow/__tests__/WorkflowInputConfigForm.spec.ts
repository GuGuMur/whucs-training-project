import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { defineComponent } from 'vue'

import WorkflowInputConfigForm from '@/components/workflow/WorkflowInputConfigForm.vue'

const stubs = {
  NCheckbox: defineComponent({
    emits: ['update:checked'],
    inheritAttrs: false,
    name: 'NCheckbox',
    props: ['checked'],
    template: '<label><input v-bind="$attrs" type="checkbox" :checked="checked" @change="$emit(\'update:checked\', $event.target.checked)" /><slot /></label>',
  }),
  NInput: defineComponent({
    emits: ['update:value'],
    inheritAttrs: false,
    name: 'NInput',
    props: ['value'],
    template: '<input v-bind="$attrs" :value="value" @input="$emit(\'update:value\', $event.target.value)" />',
  }),
  NSelect: defineComponent({
    emits: ['update:value'],
    inheritAttrs: false,
    name: 'NSelect',
    props: ['options', 'value'],
    template: '<select v-bind="$attrs" :value="value" @change="$emit(\'update:value\', $event.target.value)"><option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option></select>',
  }),
}

describe('WorkflowInputConfigForm', () => {
  it('emits updates for core input metadata', async () => {
    const wrapper = mount(WorkflowInputConfigForm, {
      global: { stubs },
      props: {
        modelValue: {
          defaultValue: '',
          key: 'query',
          kind: 'text',
          label: '查询词',
          required: false,
        },
      },
    })

    await wrapper.find('[data-testid="input-config-key"]').setValue('topic')
    await wrapper.find('[data-testid="input-config-label"]').setValue('研究主题')
    await wrapper.find('[data-testid="input-config-required"]').setValue(true)

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([
      {
        defaultValue: '',
        key: 'topic',
        kind: 'text',
        label: '查询词',
        required: false,
      },
    ])
    expect(wrapper.emitted('update:modelValue')?.[1]).toEqual([
      {
        defaultValue: '',
        key: 'topic',
        kind: 'text',
        label: '研究主题',
        required: false,
      },
    ])
    expect(wrapper.emitted('update:modelValue')?.[2]).toEqual([
      {
        defaultValue: '',
        key: 'topic',
        kind: 'text',
        label: '研究主题',
        required: true,
      },
    ])
  })

  it('resets the default value when the input kind changes', async () => {
    const wrapper = mount(WorkflowInputConfigForm, {
      global: { stubs },
      props: {
        modelValue: {
          defaultValue: '',
          key: 'payload',
          kind: 'text',
          label: '载荷',
          required: false,
        },
      },
    })

    await wrapper.find('[data-testid="input-config-kind"]').setValue('json')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([
      {
        defaultValue: {},
        key: 'payload',
        kind: 'json',
        label: '载荷',
        required: false,
      },
    ])
  })
})
