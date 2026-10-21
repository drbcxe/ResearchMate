**Day 3：把实验业务接成真正的工具调用 Agent**

今天完成真实模型、多轮交流和受控工具执行，前端能通过对话触发昨天的比较服务。预算 8 小时。

**0:00—1:00｜先理解图和工具的分工**

阅读 LovAgent graph/state.py、graphs/incoming.py 和 generation.py 的主结构，每个文件只跟一次调用。

- [ ] State 保存执行数据；Node 读写状态；Edge 指定下一步；条件边由可检查条件选择。
- [ ] 模型输出 tool_call，Python 程序执行，再把带同一 tool_call_id 的结果返回。
- [ ] 明白为什么创建一个 @tool 函数后，模型不会自动执行它。
- [ ] 画出 load_context → model → tools → model / finish；在图上标出次数上限。

参考：[LangGraph 工作流与 Agent](https://docs.langchain.com/oss/python/langgraph/workflows-agents)。

**1:00—2:30｜实现自己的状态和图**

```powershell
uv add langgraph langchain langgraph-checkpoint-postgres
```

- [ ] 迁移创建 Thread、Message、AgentRun、RunEvent 及比较证据关联。
- [ ] state.py 写清 project/thread/run/artifact、messages、tool_steps、selected_run_ids、evidence。
- [ ] context_loading.py 加载项目、当前 artifact 和最近消息；控制历史长度与单条输入上限。
- [ ] generation.py 调用模型，存在 tool_calls 时进入工具节点，再回模型。
- [ ] 工具调用累计最多 6 次，超过上限写明确错误并退出。
- [ ] incoming.py 组合主图并保存会话结果，真实错误写入 AgentRun。
- [ ] graph_trace/tool_trace 同时形成 RunEvent，暂时通过 GET 查询。
- [ ] 用当前官方 PostgreSQL checkpointer 初始化方式建立表，先实现基本对话持久化；Day 4 验证重启与中断。
- [ ] 写 scripts/init_checkpointer.py，幂等初始化该组件所需表，部署时与 Alembic 迁移分别执行。

初学阶段建议同步 graph.invoke 与同步工具；FastAPI 中同步 def 路由由其线程池执行，后台迁移到 worker 后继续用同一服务。同步 DB session 不跨线程共享。

**2:30—3:30｜实现三个首版只读工具**

- [ ] get_project_context：取项目背景与当前范围。
- [ ] list_runs：查询已选 artifact 的实验摘要。
- [ ] compare_runs：接收当前 artifact 与两个 run 标签，调用 D2 同一服务。

工具描述分别写“什么时候调用、需要哪些信息、返回什么”。参数使用类型/schema 校验；项目范围从后端上下文注入，不让模型改 project_id 或宿主文件路径。

- [ ] artifact 未选定且存在多个候选时，模型先请求明确文件。
- [ ] 不同协议这类业务错误作为 tool result 返回，让 Agent 解释拒绝。
- [ ] 工具成功时生成 evidence，数值卡片直接使用服务结果。
- [ ] 原值、改善率和来源由程序组装；模型负责说明与建议，不能凭空生成另一套数字。
- [ ] 任何工具输出都限制摘要长度，完整结果保存在 result ID 下。

**3:30—4:15｜接上真实模型**

- [ ] 复用 D1 Provider 配置，绑定真实工具。
- [ ] 温度、超时、重试预算集中配置，避免不同节点散落参数。
- [ ] 临时网络/限流错误按预算重试；非法参数与业务拒绝不盲目重试。
- [ ] 记录 model_name、prompt_version、耗时与 API 提供的 usage；没有 usage 不伪造 token 数。
- [ ] 角色 Prompt 写明：只根据项目事实与工具结果回答，区分建议/计划/执行结果。

真实手测三条：“你好”“列出当前文件里的实验”“比较 R001 和 R002”。检查工具记录，确认第三条实际调用比较服务。

**4:15—5:00｜把图封装成稳定 API**

- [ ] POST threads 创建会话。
- [ ] GET threads 与 messages 支持恢复页面。
- [ ] POST runs：保存用户消息、request_id 和执行资源，调用 chat_service。
- [ ] GET run 返回 status、reply、evidence 或 error。
- [ ] 相同 request_id 重提返回同一 run，避免双击产生两次操作。
- [ ] 同一 thread 同时运行第二条返回 THREAD_BUSY；UI 有明确等待提示。
- [ ] 当前先同步完成再返回 201，前端始终按 run_id 查状态。D5 入队后前端无需改响应结构。

**5:00—6:00｜完成真实聊天界面**

- [ ] ChatPanel：历史消息、输入框、发送、加载状态和错误。
- [ ] 新建/切换会话时带正确 project_id/thread_id。
- [ ] 返回 run_id 后读取 GET run；队列模式未接前也保持同一流程。
- [ ] 根据 evidence 展示 ComparisonCard，点击查看原结果与文件版本。
- [ ] 工具失败显示失败卡片；业务拒绝和网络异常分别显示原因。
- [ ] 发送时生成 request_id；重复点击与重连不重新生成同一请求 ID。
- [ ] “那一组”的追问能关联最近选中的 run；存在歧义时请求补充。

**6:00—7:00｜自动测试与真实验收分开**

- [ ] 使用确定性测试模型验证：直接回答、一次工具、多次工具、未知工具、非法参数、次数上限。
- [ ] 测试工具消息 ID 配对、范围检查、request 去重、THREAD_BUSY。
- [ ] 用真实 API 运行正常比较、协议不一致、追问三个场景，保存脱敏 trace。
- [ ] 固定文本测试桩只用于自动测试，界面演示的模型状态必须真实。

```powershell
uv run python -X utf8 -m pytest -q
uv run python -X utf8 scripts/verify_api.py day03
pnpm -C admin-ui build
```

scripts/verify_api.py 的真实模型模式由显式参数/配置开启，CI 默认使用测试模型，不访问真实外部 API。

**7:00—8:00｜Git 与当天演示**

分支 feat/day03-agent-chat。

- [ ] 提交图、工具、Provider、迁移、聊天前端和测试；附上对话请求与工具结果证据。
- [ ] PR 检查通过并合并。
- [ ] docs/day03.md 记录实际模型名、工具选择、错误边界和真实 API 耗时。
- [ ] 独立解释：如果删除工具结果，仅让模型自己算数，会失去哪些可靠性。

当天结束可展示：浏览器发送自然语言 → 看到实际工具记录 → 展示有来源的比较卡片 → 多轮追问。

