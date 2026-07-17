# 完整 Vue Flow 编排实现计划

## 目标

将 `/workflow` 从当前仅展示智能体任务控制台、但保留大量未渲染设计器代码的状态，收敛为一个可创建、加载、编辑、连线、配置、保存、校验、发布、执行和逐步调试的可视化 DAG 编排器。图编辑状态必须只有一个权威来源，前后端图定义必须可无损往返，发布与执行必须以服务端校验为准。

## 当前代码结论

1. `/workflow` 确实指向 `WorkflowBuilderView.vue`，但模板只渲染智能体任务控制台；现有测试明确断言 Vue Flow 画布隐藏。设计器脚本与大量 CSS 因而成为不可达代码。
2. `WorkflowBuilderView.vue` 同时承担页面布局、Vue Flow 状态、节点配置、序列化、校验、持久化、执行态、调试态和智能体任务控制台，职责过载。
3. 主页面使用 `useWorkspaceStore()`，而项目已有 `useWorkflowStore()`；两个 store 都维护工作流列表、当前项、校验和执行状态，存在双重事实源。
4. 设计器没有 `@connect`/`addEdges`，没有节点或边删除入口，也没有自定义节点中的 `Handle`，所以用户无法完成基本图编辑闭环。
5. `list_workflows()` 返回 `node_count=0, nodes=[], edges=[]`，从列表重新打开工作流会丢失图定义；当前 API 又没有 `GET /workflows/{id}`。
6. 前端有本地校验，但“校验”按钮未调用服务端校验；发布流程没有强制服务端校验，执行也允许未发布或未校验定义。
7. 后端调试接口固定模拟 3 个 `Node-N`，不执行真实拓扑节点；前端“单步调试”调用的是智能体任务 API，而不是工作流 debug API。
8. 后端声明支持 `condition/loop/transform/aggregate`，但执行器对这些类型只是透传参数，没有分支、循环或聚合语义。前端不应在实现语义前把它们作为可用节点承诺给用户。
9. 图序列化会丢弃边的 label/type，并强制 handle 为 null；模板读取又接受这些字段，往返不对称。触发器命名也存在 `file_uploaded` 与种子模板 `file_upload` 不一致。
10. 节点参数绑定的核心能力已有基础：literal/input/node/ref 可以被后端解析；但前端表达式模式序列化为 `mode: ref`，需要统一领域命名与校验规则。

## 目标架构与组件边界

- `WorkflowBuilderView.vue`：仅负责路由级布局、加载流程与工具目录、组合下列组件。
- `WorkflowListPanel.vue`：草稿/已发布/模板列表，选择、复制模板、新建入口。
- `WorkflowToolbar.vue`：名称、触发方式、脏状态、保存、校验、发布、执行、撤销/重做。
- `WorkflowCanvas.vue`：唯一 Vue Flow provider；负责拖放、连接、选择、键盘删除、缩放和视口，不直接调用 API。
- `WorkflowNode.vue`：统一节点外观与输入/输出 `Handle`；按节点类型显示状态和错误。
- `WorkflowNodeInspector.vue`：选中节点的名称、工具、输入块和参数绑定编辑，props 下发、事件上抛。
- `WorkflowValidationPanel.vue`：合并本地即时问题与服务端权威问题，并可定位节点/边。
- `WorkflowRunPanel.vue`：运行输入表单、执行时间线、节点输入输出与失败详情。
- `WorkflowDebugPanel.vue`：真实 debug session、逐步执行、当前节点与上下文快照。
- `AgentTaskConsole.vue`：保留现有自然语言智能体任务能力，但与 DAG 设计器分成独立页签，不再与图状态耦合。
- `useWorkflowDesigner.ts`：图领域状态与动作，包括 hydrate/serialize/add/connect/remove/update/select/dirty/undo/redo；不负责远程请求。
- `stores/workflow.ts`：工作流远程实体、选中 ID、校验/发布/执行/调试请求状态；移除 workspace store 中重复的 workflow 写路径。
- `workflowDesignerTypes.ts` 与 `workflowCodec.ts`：前后端 DTO、Vue Flow Node/Edge、参数绑定之间的唯一双向转换边界。

## 分阶段实施

### 阶段 1：锁定契约与回归测试

- 为后端补充工作流详情读取，或修改列表保证返回完整图；优先新增 `GET /api/v2/workflows/{id}`，列表只返回摘要，避免列表载荷膨胀。
- 增加版本/更新时间字段与乐观并发条件，至少防止旧画布静默覆盖新版本。
- 统一 trigger 枚举：`manual | file_upload | schedule | websocket`。
- 明确首期可执行节点只包含 `input | trigger | tool | output`；其余类型在具备真实运行语义前隐藏或标记“未支持”。
- 先写失败测试覆盖：图详情无损读取、非法边/重复 ID/空图/未知工具/环、未校验发布、未发布执行、参数绑定错误、权限边界。

验收：同一工作流 create → get → update → get 后 nodes、edges、position、handles 和参数绑定结构等价。

### 阶段 2：建立单一状态源与无损 codec

- 启用 `useWorkflowStore()` 作为远程工作流唯一 owner，删除或委托 `useWorkspaceStore()` 中重复动作。
- 新建 `useWorkflowDesigner()`，用 `shallowRef` 保存 Vue Flow 图数组，通过不可变替换触发更新；所有图变更只能经 typed actions。
- 实现 `fromWorkflowDefinition()` / `toWorkflowPayload()`，完整保留节点类型、位置、tool_name、parameters、edge handles、label/type（后端 schema 同步支持）。
- 增加 `baselineHash`/`isDirty`、保存成功后的基线更新、切换流程与离开路由时的未保存确认。
- 节点 ID 使用稳定 UUID；边 ID 从连接生成且防止重复、自环和非法方向。

验收：加载现有流程、移动节点、修改参数、保存并刷新后完全复原；workspace store 与 workflow store 不再出现双份可变工作流状态。

### 阶段 3：恢复完整 Vue Flow 画布交互

- 将不可达设计器模板拆成 `WorkflowCanvas` 等组件并重新挂载到 `/workflow` 的“可视化编排”页签。
- 使用 Vue Flow 标准 controlled flow：处理 `nodes-change`、`edges-change`、`connect`、drop、selection-change。
- 自定义节点渲染 `Handle`；限制 input/trigger 无入边、output 无出边，并按节点能力限制多入/多出。
- 支持节点/边选中、Delete/Backspace 删除、工具栏删除、画布空白取消选择、fit view、MiniMap、Controls。
- 增加撤销/重做，覆盖新增、删除、移动、连线和参数修改；拖动仅在结束时写历史，避免历史栈爆炸。
- 增加空态、新建空流程、从模板复制；模板本体只读，复制后进入草稿编辑。

验收：纯 UI 测试可完成“拖入 input → 拖入 tool → 连接 → 配置 → 删除/撤销 → 保存”的完整闭环。

### 阶段 4：节点配置和数据绑定正确化

- 输入节点支持 text/number/json/file/knowledge_base，校验 key 唯一、必填项和 JSON 合法性。
- 工具节点完全由工具 `input_schema` 生成编辑器；字符串、数字、布尔、数组、对象分别使用类型正确的控件，避免所有 literal 都退化为字符串。
- 参数可选择 literal、workflow input、可达上游 node output、expression/ref；只允许引用拓扑上游，删除/改名后检测悬空引用。
- 后端工具定义增加输出 schema，前端不再硬编码 `result/summary` 两个输出路径。
- 首期 output 节点只负责选择并输出上游值；condition/loop/aggregate 等在后端实现真实语义后分批开放。

验收：calculator 从 workflow input 取 expression，输出节点绑定 calculator result，执行得到类型正确的 14；非法/下游/不存在引用无法发布。

### 阶段 5：服务端权威校验、发布与版本生命周期

- 本地校验用于即时提示；保存后调用服务端校验并将 `node_id/edge_id` 映射回画布高亮。
- 发布动作执行“保存脏草稿 → 服务端校验 → 校验通过后发布”，任一步失败都不改变本地发布态。
- 后端 publish 必须内部再次校验，不能相信前端；execute 默认只允许 published 版本。
- 发布生成不可变版本快照；再次编辑从发布版本创建新草稿或明确降为 draft，避免已发布定义被原地修改。
- 增加版本列表与版本详情/恢复接口，替换当前仅存在内存中的 `versionLog`。

验收：刷新浏览器后仍能查看真实版本历史；无效图不能通过直接 API 发布；执行固定使用一个已发布快照。

### 阶段 6：真实执行与逐步调试

- 增加执行记录列表/详情接口并持久化 execution 与 node execution，而不是只返回一次性响应。
- `run` 根据 input 节点动态生成表单，提交后按 node_id 将 pending/running/success/failed 映射到画布。
- 将 debug start/step 改为真实拓扑游标：保存 session 的输入、节点输出、当前索引和失败状态，每一步调用与正式执行相同的节点执行函数。
- 增加 debug cancel/finish 与过期清理；前端不再用 agent task 伪装 workflow debug。
- 条件、循环等高级节点若要开放，必须在此阶段分别定义确定性的执行、分支边语义、最大迭代和失败策略。

验收：同一已发布 DAG 的正常执行与逐步调试产生一致的节点输入输出；失败节点可定位、可查看错误，后续节点保持未执行。

### 阶段 7：测试、性能和可用性收口

- 单元测试：codec、DAG/引用校验、designer actions、undo/redo、store 并发与错误恢复。
- 组件测试：palette、canvas connect/delete、inspector、validation 定位、run/debug panels。
- 后端测试：详情、版本、发布门禁、执行持久化、真实 debug、权限与并发冲突。
- E2E：新建并执行 calculator 流程；模板复制；刷新恢复；环路发布失败；调试失败节点。
- 运行 `pnpm vitest run`、`pnpm type-check`、`pnpm build` 与后端全套 pytest；浏览器检查桌面端和移动端。移动端提供查看/运行，复杂编排可明确限制为桌面端。
- 大图只在正确性完成后优化：避免深层 Vue proxy，节点配置面板按选中节点渲染，拖动期间节流持久状态更新。

## 推荐实现顺序

先完成阶段 1–3，得到真正可编辑且可持久化的 Vue Flow；再完成阶段 4–5，保证参数与发布正确；最后做阶段 6–7，把执行、调试和质量闭环补齐。不要先继续扩充新节点类型，因为当前最基础的连接、删除、重新加载和服务端校验链路尚未闭合。

## 完成定义

- 可视化设计器在 `/workflow` 可见，智能体任务控制台作为独立页签保留。
- 任意已支持图可以无损加载、编辑、保存、刷新恢复。
- 图只能通过统一 designer actions 变更，远程实体只由 workflow store 管理。
- 服务端拒绝无效发布与未发布执行；前端准确定位问题。
- 正式运行和单步调试共享相同执行语义，并有可恢复的历史记录。
- 前后端契约、单元测试、组件测试、E2E、类型检查和构建全部通过。
