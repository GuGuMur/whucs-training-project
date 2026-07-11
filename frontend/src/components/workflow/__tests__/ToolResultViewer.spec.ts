import { shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ToolResultViewer from '@/components/workflow/ToolResultViewer.vue'

const global = {
  stubs: {
    NEmpty: { template: '<div><slot />暂无结果</div>' },
    NStatistic: { props: ['label', 'value'], template: '<div>{{ label }}{{ value }}</div>' },
    NTag: { template: '<span><slot /></span>' },
  },
}

describe('ToolResultViewer', () => {
  it('renders mixed multi-tool results with sections and key results', () => {
    const wrapper = shallowMount(ToolResultViewer, {
      global,
      props: {
        finalAnswer: '已完成多步骤任务',
        resultView: {
          type: 'mixed',
          content: '已完成多步骤任务',
          tools: ['calculator', 'course_lookup'],
          key_results: ['计算结果是 5。', '查询到课程：算法设计'],
          sections: [
            { tool: 'calculator', observation: '计算结果：5' },
            { tool: 'course_lookup', observation: '算法设计（CS101，王老师）' },
          ],
        },
      },
    })

    expect(wrapper.text()).toContain('mixed')
    expect(wrapper.text()).toContain('计算结果是 5')
    expect(wrapper.text()).toContain('查询到课程：算法设计')
    expect(wrapper.text()).toContain('calculator')
    expect(wrapper.text()).toContain('course_lookup')
    expect(wrapper.text()).toContain('算法设计（CS101，王老师）')
  })

  it('renders chart result summaries for data tools', () => {
    const wrapper = shallowMount(ToolResultViewer, {
      global,
      props: {
        finalAnswer: '数据文件包含 2 行。',
        resultView: {
          type: 'chart',
          content: '数据文件包含 2 行。',
          chart: {
            kind: 'bar',
            series: {
              score: { min: 80, max: 95, avg: 87.5 },
            },
          },
          key_results: ['行数：2'],
        },
      },
    })

    expect(wrapper.text()).toContain('chart')
    expect(wrapper.text()).toContain('score')
    expect(wrapper.text()).toContain('avg: 87.5')
    expect(wrapper.text()).toContain('行数：2')
  })
})
