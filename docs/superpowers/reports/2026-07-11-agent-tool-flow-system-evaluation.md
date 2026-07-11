# Agent Tool-Flow System Evaluation

## Scope
This report covers the v2 agent tool-flow implementation after the production LLM/tool-flow refactor on 2026-07-11.

The automated backend acceptance test is:

- `backend/tests/test_agent_evaluation.py::test_agent_tool_flow_evaluation_covers_25_acceptance_cases`

It runs the real `AgentExecutor`, deterministic fallback `AgentPlanner`, and `ToolRegistry` against a controlled workspace fixture. The test does not call a live LLM, so planner behavior is reproducible in CI.

## Scenario Coverage
The test covers 25 cases:

1. Direct answer without tools.
2. Calculator addition.
3. Calculator expression with parentheses.
4. Invalid calculator expression.
5. Course lookup success.
6. Course lookup no result.
7. Missing course query clarification.
8. File content search hit.
9. File content search no result.
10. File content permission denial.
11. File metadata query by failed parse status.
12. File metadata query by tag/name condition.
13. CSV analysis through `python_data`.
14. CSV permission denial.
15. RAG query success.
16. RAG missing KB clarification.
17. RAG KB permission denial.
18. Database query over whitelisted files.
19. Database query over whitelisted knowledge bases.
20. Weather query with provider unconfigured.
21. Multi-tool task: calculator plus course lookup.
22. Multi-tool task: file search plus CSV analysis.
23. Multi-tool task: calculator plus file search.
24. Multi-turn direct follow-up with history context.
25. Invalid database table request guarded by clarification.

## Metrics
Acceptance targets:

- Task completion/status match rate: >= 85%.
- Tool selection accuracy: >= 85%.
- Argument accuracy: >= 85%.
- Grounded answer/context check rate: >= 85%.
- Latency metadata coverage for tool calls: >= 85%.
- Unauthorized data exposure: 0 accepted permission-denial failures.

Current focused verification:

- Task status match: 25/25.
- Tool selection accuracy: 25/25.
- Argument accuracy: 25/25.
- Grounded/context answer checks: 25/25.
- Tool-call latency metadata coverage: 25/25.
- Permission-denial cases return failures or clarification without exposing file/KB contents.
- Plan preview and risk-confirmation behavior passes focused executor/frontend store tests.
- SSE agent task streaming passes focused backend event and frontend store tests.

## Typical Successes
- Multi-step natural-language tasks produce ordered tool calls in one task, such as `calculator -> course_lookup`.
- Tool execution traces expose `understand`, `plan`, repeated `call`/`observe`, and final `answer` phases.
- Tool-call steps include status, arguments, outputs, and `latency_ms` metadata for UI transparency.
- RAG, file metadata, database, CSV, and weather-provider error paths are part of the same executor flow.
- Multi-turn direct follow-up uses prior message history instead of ignoring conversation context.

## Typical Failure/Guidance Cases
- Missing course names return `needs_clarification` with a clear prompt.
- Missing RAG `kb_id` returns `needs_clarification`.
- Invalid calculator expressions return `failed` with a parameter-oriented error.
- Unauthorized file and KB access returns `failed` without exposing protected content.
- Weather queries fail clearly when `WEATHER_API_URL` is not configured instead of returning mock weather.

## Known Limitations
- The acceptance test intentionally disables live LLM planning for determinism; live LLM behavior is covered by planner JSON parsing/repair tests, not by this 25-case suite.
- Weather success depends on operator configuration of a real `WEATHER_API_URL`; the default local test only verifies the no-mock failure path.
- Risk-confirmation and SSE streaming are covered by focused tests, while the 25-case acceptance matrix remains deterministic and non-streaming so its metrics stay stable.
