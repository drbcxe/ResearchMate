**Day 4：让 Agent 跨天可继续，并接好登录与记忆页面**

今天完成：登录、偏好修订、跨会话读取、重启恢复和一次真实中断继续。预算 8 小时。

**0:00—0:30｜看懂持久化的两层**

- [ ] 阅读 LovAgent memory_service.py 的读记忆/更新入口，区分聊天记录与画像。
- [ ] 阅读自己的 D3 状态，标出哪些只属于一次会话，哪些应跨会话保存。
- [ ] checkpointer 保存图执行；Memory 表保存可修订偏好；项目与实验表保存事实。
- [ ] 不把内存字典或浏览器 localStorage 当作跨服务重启的后端记忆。

参考：[LangGraph 持久化](https://docs.langchain.com/oss/python/langgraph/persistence)。

**0:30—2:00｜实现可纠正记忆**

- [ ] Memory 迁移包含 source_message_id、revision、is_active、supersedes_id。
- [ ] 第一版支持有限 key：preferred_metric、response_length、report_language；项目背景继续由项目资料维护。
- [ ] memory_service 实现列出、创建、修订、停用，以及按当前项目读取生效值。
- [ ] 同一 key 新修订使旧记录停止生效；expected_revision 过时返回 REVISION_CONFLICT。
- [ ] DELETE 的语义是停止该偏好召回，保留原始聊天历史与修订审计；页面写清这一点。
- [ ] revise_memory 工具仅处理用户明确表达的偏好，来源来自当前真实用户消息。
- [ ] generation 读取生效偏好，优先级高于已被替代的旧聊天描述。
- [ ] 新会话可以读取同项目偏好，P001 项目偏好不带进 P002。
- [ ] 这周先不做从所有普通聊天中自动抽取研究事实。

**2:00—3:00｜验证持久化与中断**

- [ ] graph.compile 使用 PostgreSQL checkpointer，thread_id 与数据库 Thread 对应。
- [ ] 历史按完整轮次裁剪，ToolMessage 与原 tool_call 一起保留；对历史长度设上限。
- [ ] 单条用户输入和工具摘要也有长度限制，原始 CSV 不塞入 Prompt。
- [ ] 选择一个确定中断场景：项目有多个 CSV，用户要求比较但没选文件。
- [ ] 在任何有副作用操作前，缺信息节点调用 interrupt，返回“选择文件”及合法选项。
- [ ] UI 展示选择表单；POST resume 校验项目归属后用 Command(resume=...) 继续同一 thread。
- [ ] 恢复前后同一操作的动作键保持一致，节点重放不重复创建数据。
- [ ] 等待时重启 API，回来补充后仍能完成。

不要仅显示“请补充”文本就宣称实现了 graph interrupt。需要记录 checkpoint、needs_input 状态与 resume 的实际调用。[中断机制](https://docs.langchain.com/oss/python/langgraph/interrupts)

**3:00—4:00｜实现单用户登录**

```powershell
uv add itsdangerous
```

- [ ] SessionMiddleware 使用 .env 的 SESSION_SECRET。
- [ ] 实现 login/logout/me，ADMIN_PASSWORD 只在后端读取，不返回前端。
- [ ] 登录 Cookie 为 HttpOnly、SameSite=Lax；本地 HTTP 与未来 HTTPS 的 Secure 配置分开。
- [ ] 所有项目、文件、聊天、记忆、任务、通知与执行 API 应用同一 require_admin；健康检查和最小配置状态可匿名。
- [ ] 写入请求检查可信 Origin，并只允许配置的本地开发/部署地址。
- [ ] 数据库若不需要保存账号，保持固定本地管理员这一明确范围。
- [ ] 前端未登录显示 LoginForm，401 时返回登录状态，不继续显示旧项目内容。

登录后 API 手测需要会话：

```powershell
$rmLoginBody = @{password='填写你本机.env中的密码'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/auth/login' -Method Post -ContentType 'application/json' -Body $rmLoginBody -SessionVariable rmSession
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/projects' -WebSession $rmSession
```

把脚本中的实际密码改为从环境或交互读取，不将真实值写进提交或日志。

**4:00—5:30｜完成三个前端行为**

- [ ] LoginForm：密码、错误提示、请求中状态；顶部退出按钮。
- [ ] MemoryPanel：生效值、来源与 revision；修改/停用后重新读取。
- [ ] SettingsPanel：模型名、配置是否齐全、角色说明和应用版本，提示 Key 在后端 .env 配置。
- [ ] 加“检测模型”按钮，调用受保护的 POST /api/settings/check-model，复用 D1 预检服务，显示真实连通/工具能力/耗时；请求中禁止重复点击。
- [ ] ChatPanel 接需要补充信息的卡片；补充后继续同一执行。
- [ ] 刷新或重新登录后加载会话列表与历史，不只恢复浏览器中的文字。
- [ ] 修改记忆后再次提问，确认后端 Prompt 使用新值；旧值停用后不继续召回。

**5:30—7:00｜重点测“跨次是否还正确”**

- [ ] 用户“记住我优先看 RMSE”，新建会话能读取。
- [ ] 修改成 MAE，新会话使用 MAE，旧记录有被替代关系。
- [ ] 停用后不再读取该偏好。
- [ ] API 重启后会话与记忆都在。
- [ ] 中断等待 → 重启 → resume → 完成，记录同一个 thread。
- [ ] 未登录请求被拒绝；登录与退出流程真实有效。
- [ ] 同名偏好在两个项目中不互相覆盖。
- [ ] 过时 revision 更新被拒绝，前端刷新并展示当前值。

```powershell
uv run python -X utf8 -m pytest -q
uv run python -X utf8 scripts/verify_api.py day04
pnpm -C admin-ui build
```

脚本从配置登录后再测试。测试 session secret 与测试密码独立于真实 .env。

**7:00—8:00｜Git 与复盘**

分支 feat/day04-memory-recovery。

- [ ] PR 包含登录与所有受保护路由检查、记忆迁移、UI、恢复用例。
- [ ] 所有开发环境的 Key/密码仍被忽略。
- [ ] docs/day04.md 记录新会话、改偏好、重启和中断恢复的结果。
- [ ] 解释：为什么图检查点不能替代实验结果表；为什么恢复节点前后的写入要去重。

当天结束可展示：登录 → 保存偏好 → 新会话读取 → 修改偏好 → 中断选择文件 → 重启后继续。

