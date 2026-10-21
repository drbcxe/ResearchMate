**Day 6：补实时过程、重连和前后端故障行为**

今天把已完成的功能做成连贯、可恢复的工作台。预算 8 小时。今天主要联调与修复，不再扩展业务种类。

**0:00—0:30｜固定事件协议**

- [ ] 复述：创建执行用 POST runs，查看持久化事实用 GET run，实时观察用 GET events。
- [ ] SSE 只是传输方式，连接断开不等于后台任务取消。
- [ ] EventSource 自动重连，因此终态要 close，重复 sequence 要去重。
- [ ] 既有 /api Vite 代理和 Cookie 会话继续使用，不新引入另一套跨域协议。

**0:30—2:00｜后端 SSE 与结构化记录**

- [ ] context/tool/reply 等事件先写 RunEvent，再给 SSE 读取。
- [ ] id 为 sequence；data 为 JSON，以空行结束。
- [ ] 新连接读取 after 或 Last-Event-ID 后的事件，再观察新记录。
- [ ] 心跳保持连接；运行结束输出最终事件并结束服务端生成器。
- [ ] 查询前检查当前登录和项目范围；不能凭 run UUID 读取其它项目。
- [ ] 异步 SSE 生成器不直接执行长期同步数据库/模型阻塞操作；使用适当线程封装或独立查询方式。
- [ ] request_id、run_id、thread_id、tool_call_id、comparison_id 在日志中可关联。
- [ ] 业务错误与系统异常使用统一响应，日志记录堆栈时不带 Key。
- [ ] 保存模型/提示词/代码版本和实际可取得的 usage。

第一版必须有步骤流与最终答复。逐 token 增量若锁定 SDK/模型组合支持，可在已通过的事件协议上增加 reply.delta；否则在界面如实显示步骤和最终回复，不能伪造 token 流。

**2:00—3:30｜前端事件、刷新和错误状态**

- [ ] useRunEvents 或等效 hook 订阅当前 run。
- [ ] tool.started/finished 显示业务工具卡片与结果摘要。
- [ ] needs_input 显示 D4 的补充表单，提交后继续同一 thread。
- [ ] reply.completed 更新最终消息；run.failed 显示错误及可执行处理。
- [ ] 收到终态 close EventSource，卸载组件也清理连接。
- [ ] 按 sequence 去重，避免重连时同一消息出现两次。
- [ ] 刷新后先 GET run/messages，再续读事件；数据库是最终事实来源。
- [ ] 项目切换时关闭旧连接，清空旧结果与旧 artifact 引用。
- [ ] 登录失效回登录页面，后台执行保留真实状态。
- [ ] 两个输入同时提交时正确处理 THREAD_BUSY。

**3:30—5:30｜建立 20 项最终验收与自动回归**

将本目录总验收清单 C01—C20 转成 scripts/run_acceptance.py 和相关 pytest/Playwright 场景。现有 evals/scenarios.json 包含第二阶段项，按映射执行，不能把未来 MCP/模型/检索场景记成当前已通过。

建议分层：

- [ ] 纯计算/契约：已有比较测试＋缺字段、非有限数值、不同口径。
- [ ] DB/API：项目范围、文件事务、记忆修订、request 去重、登录。
- [ ] 图：工具选择、参数、ToolMessage 配对、次数上限、中断恢复。
- [ ] 后台：真实队列暂停恢复、重复事件、提醒改期/取消/补发。
- [ ] 浏览器：登录 → 建项目 → 上传 → 比较 → 对话 → 改记忆 → 创建/取消提醒。
- [ ] 页面断网/刷新：后台状态不被误改，重连无重复消息。
- [ ] 真实模型手测：正常、拒绝、追问与记忆，单独记录，不能仅用测试桩替代。

```powershell
pnpm -C admin-ui add -D @playwright/test
pnpm -C admin-ui exec playwright install chromium
uv run python -X utf8 -m pytest -q
pnpm -C admin-ui build
pnpm -C admin-ui exec playwright test
```

配置 Playwright baseURL 为当前测试前端地址；测试库与测试账号固定为测试专用。CI 可使用确定性模型和 eager 执行跑业务回归，但真实 Celery/真实模型仍须单列验收结果。

**5:30—7:00｜修复影响可用性的缺口**

按严重程度：

1. 结果错误、跨项目取错数据、状态虚报成功。
2. 重启丢任务、提醒重复或取消后仍发送。
3. 交互无法继续、登录/断线后页面卡住。
4. 表格、图表和布局影响阅读。

- [ ] 每发现一个具体问题，先记录复现，再修复并增加对应回归。
- [ ] 检查所有可点击按钮都有真实后端行为。
- [ ] 请求中防重复点击；空数据、无实验、加载失败均有明确界面。
- [ ] 支持较长消息和结果表格，窄屏不遮住操作。
- [ ] 不为了 UI 装饰更换整套组件或框架。

**7:00—8:00｜Git、CI 和验收报告**

分支 feat/day06-streaming-hardening。

- [ ] CI 检查 Ruff、Python 测试、前端类型/构建。
- [ ] CI 中执行的浏览器/数据库用例写明服务启动方式和测试模型模式。
- [ ] scripts/run_acceptance.py 输出 case_id、预期、实际、pass/fail、证据位置。
- [ ] 测试失败保留错误信息，清单状态按真实结果更新。
- [ ] 提交 PR，合并后 docs/day06.md 附完整验收结果与待修项。

当天结束可展示：运行中看到真实步骤 → 刷新/断开再回到执行 → 不重复显示 → 失败能定位 → 恢复后继续。

