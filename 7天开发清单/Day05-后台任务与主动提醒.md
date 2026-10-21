**Day 5：让聊天后台执行，让待办到期真正产生提醒**

今天完成真实 Celery 队列、待办操作、持久化提醒和站内通知。预算 8 小时。所有用户操作有页面入口。

**0:00—0:30｜先区分三件事**

- [ ] TodoTask 是用户计划做的事，状态 todo/done/cancelled。
- [ ] AgentRun 是程序的一次执行，状态 queued/running/needs_input/succeeded/failed。
- [ ] Reminder 是在指定时刻检查/跟进某个待办，送达记录独立。
- [ ] 阅读 LovAgent proactive_chat_service.py 中“何时触发”和发送日志的处理，记下你要实现的时间、停止和重复规则。

这里不把计划实验显示成已运行，也不把提醒已触发显示成用户已读。

**0:30—1:30｜把执行移到 Linux worker**

```powershell
uv add celery redis
```

- [ ] 写 app/tasks/celery_app.py、chat_tasks.py，任务仅接 run_id，从数据库加载输入。
- [ ] worker 内创建独立 DB session/checkpointer，调用 D3/D4 的同一 chat_service。
- [ ] POST runs 改为事务写 queued 资源和 Outbox 后返回 201，界面按已有 run_id 查询状态。
- [ ] 补一个执行 action key 与唯一约束，重复消息不重复执行已完成写入。
- [ ] 一个 thread 同时只允许一个活动执行。
- [ ] Compose 添加 worker 和 beat，复用同一应用代码/依赖镜像；Windows 宿主不直接跑 Celery。
- [ ] 今天先完成 Python 基础镜像与开发 Compose 挂载，D7 加生产前端构建。
- [ ] broker 使用 redis 服务地址，数据库使用 postgres 服务地址。

容器中等效命令由 Compose command 设置：

```text
uv run celery -A app.tasks.celery_app worker --loglevel=INFO --concurrency=1
uv run celery -A app.tasks.celery_app beat --loglevel=INFO
```

beat 只有一个实例。普通 Python 单元测试的 eager 模式不能替代真实 worker 验收。[Celery FAQ](https://docs.celeryq.dev/en/stable/faq.html)

**1:30—3:00｜实现待办和提醒服务**

- [ ] 迁移创建 TodoTask、Reminder、Outbox、Delivery/Notification。
- [ ] 实现待办创建/列出/完成/取消 API，修改检查 revision。
- [ ] 实现提醒创建、改期、取消 API；响应包含确定日期、时间、时区和 revision。
- [ ] 时间用 datetime aware，数据库存 UTC，界面明确显示 Asia/Shanghai。
- [ ] 提醒只能关联本项目待办，过期或已完成待办不默认新建提醒。
- [ ] 用户明确说“明天九点提醒”时登记；信息不足时请求补充，不自行猜一个时间。
- [ ] create_followup、update_followup、cancel_followup 工具调用同一服务。
- [ ] create_task、update_task 处理不带提醒的待办；一句话要求两者时按先建待办、再用返回 ID 登记提醒执行。get_task_status 查询待办与关联提醒，不改变 AgentRun 状态。
- [ ] 明确请求已经是授权，不对每个普通登记操作再次问确认。
- [ ] 日常含糊表达如“明天再看看”不自动变成提醒。

**3:00—4:00｜实现主动流程和恢复扫描**

- [ ] beat 每 15 秒调度扫描任务，动态 due_at 以 PostgreSQL 为准，不只存在内存或 Redis ETA。
- [ ] outbox 扫描分发待投递执行，消息投递失败保留事件等待下一次扫描。
- [ ] worker 原子认领任务，使用 lease_until；步骤执行时更新租约/进度。
- [ ] 租约过期后按预算恢复或失败，错误可查询，不无限停留 running。
- [ ] 主动图先读取当前 Task/Reminder，再检查 revision、取消与完成状态。
- [ ] 根据真实待办生成一条简短提醒；模型超时或不可用时使用事实模板。
- [ ] 写 Notification 前在事务内再次检查当前 revision 和状态。
- [ ] 唯一 event_id 由 reminder_id＋revision 形成，重复事件返回既有通知。
- [ ] 只有通知已落库可查询，才标记站内送达。
- [ ] 24 小时内过期提醒补发，超过 24 小时标 expired；页面能查原因。
- [ ] 重试预算按执行记录控制，避免 HTTP、图、队列无边界叠加重试。

**4:00—5:30｜前端任务与通知闭环**

- [ ] TaskPanel：新建、查看、完成、取消待办。
- [ ] 每个待办提供设置提醒、改期、取消提醒，显示具体时间与状态。
- [ ] 时间输入明确采用本地 Asia/Shanghai，提交 ISO 时间含时区。
- [ ] NotificationPanel：未读数量、列表、关联任务、标记已读。
- [ ] 站内通知每 5 秒轮询一次；页面卸载清定时器，登录失效停止请求。
- [ ] ChatPanel 在 queued/running 时显示真实状态，刷新后按 run_id 重新查询。
- [ ] 任务完成后看到提醒停止条件已生效。
- [ ] 错误不伪装成成功 Toast，成功操作读回后端状态。

**5:30—7:00｜用短时间与故障验证**

先把 Compose 中今天实现的 api/worker/beat 启动，数据库迁移完成后再启动消费者。API 模式与 Docker 模式不要同时占用同一端口。

```powershell
docker compose up -d postgres redis
uv run alembic upgrade head
docker compose up -d --build api worker beat
docker compose ps
docker compose logs --tail 80 worker beat
```

迁移必须针对同一个数据库。最终 D7 改成清晰的容器内迁移启动顺序。

- [ ] 在界面创建当前时间 60 秒后的提醒；在本机实测到期后 60 秒内可查询，记录实际延迟。
- [ ] 到期前改期，旧时间不产生通知；到期前取消也不产生。
- [ ] 标记待办 done 后，关联提醒停止。
- [ ] 同一事件处理两次，只有一条可见通知。
- [ ] 提醒待触发时 stop api worker beat，超过到期再启动，按补发策略处理。
- [ ] 暂停 worker 后发聊天，状态 queued；恢复 worker 后完成。
- [ ] 模拟模型超时，执行失败/回退符合声明，页面不挂死。
- [ ] 模拟租约过期，用测试时钟加速恢复测试；不要为了测它真实等几小时。

**7:00—8:00｜Git 与复盘**

分支 feat/day05-tasks-reminders。

- [ ] 单元测试与数据库测试覆盖时间、revision、唯一键和停止条件。
- [ ] 真实 Compose/worker 验收记录单列，不能只写 eager 测试通过。
- [ ] uv.lock、迁移、worker/beat 配置、前端和测试入 PR。
- [ ] docs/day05.md 记录 due_at、实际处理时间、event_id、是否重复。
- [ ] 看日志仅取测试摘要，不上传用户数据、Key 或完整配置。

当天结束可展示：对话创建待办与提醒 → 改期/取消 → worker 后台处理 → 到期出现一条通知 → 重启后仍能处理未完成项。

