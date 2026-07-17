import { afterEach, describe, expect, it, vi } from 'vitest'

import { streamAgentTask } from '@/client/workspace'

const encoder = new TextEncoder()

function streamResponse(chunks: string[]) {
  return new Response(new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  }), {
    headers: { 'Content-Type': 'text/event-stream' },
    status: 200,
  })
}

describe('streamAgentTask', () => {
  afterEach(() => vi.restoreAllMocks())

  it('delivers a terminal done event when the final SSE frame has no trailing newline', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(streamResponse([
      'data: {"type":"plan","step":{"type":"thought","phase":"plan","title":"计划","content":"执行计划","status":"success"}}\n\n',
      'data: {"type":"done","task":{"id":"task-1","task":"测试","status":"completed","steps":[],"final_answer":"执行完成","result_view":{"type":"text","content":"执行完成"}}}',
    ]))

    const events = []
    for await (const event of streamAgentTask('token', { task: '测试' })) events.push(event)

    expect(events.map((event) => event.type)).toEqual(['plan', 'done'])
    expect(events[1]?.task?.final_answer).toBe('执行完成')
  })

  it('accepts SSE data fields without a space after the colon', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(streamResponse([
      'data:{"type":"error","message":"执行器失败"}\n\n',
    ]))

    const events = []
    for await (const event of streamAgentTask('token', { task: '测试' })) events.push(event)

    expect(events).toEqual([{ type: 'error', message: '执行器失败' }])
  })
})
