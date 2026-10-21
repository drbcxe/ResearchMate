**Day 2：完成项目、CSV 导入与实验比较的前后端**

今天完成一条不依赖 LLM 的真实业务链路：创建项目 → 上传文件 → 看实验 → 比较 → 看来源。预算 8 小时。

**0:00—0:30｜先学够今天需要的概念**

- [ ] 理解 HTTP 路由、Pydantic 输入模型、ORM 模型、事务和 Alembic 迁移的不同职责。
- [ ] 阅读 LovAgent app/models/user.py 中用户/会话表和一个 service 的读写，不照搬其数据字段。
- [ ] 复述：文件保存在哪里、元数据保存在哪里、比较计算在哪里完成。

**0:30—1:30｜建立数据库与迁移**

```powershell
uv add sqlalchemy 'psycopg[binary,pool]' alembic python-multipart
uv run alembic init migrations
```

- [ ] repositories/database.py 创建 engine 和按请求/任务独立使用的 Session。
- [ ] 写 Project、Artifact、ExperimentRun；比较输出增加持久化结果表，或复用有明确类型的 ToolResult 表。
- [ ] Project ID 使用 P001 这类项目代码；artifact UUID 与文件中的 run_id 标签分开。
- [ ] migrations/env.py 导入全部模型元数据，从 Settings 读取 URL。
- [ ] 生成迁移前检查内容，确认包含预期表和唯一约束。

```powershell
uv run alembic revision --autogenerate -m 'create projects artifacts experiments and comparison results'
uv run alembic upgrade head
uv run alembic current
```

自动生成不是自动正确。新迁移升级到全新测试库也要通过，测试库名称与开发库分开。

**1:30—3:00｜写服务层，复用已有比较规则**

- [ ] project_service：创建项目、重复 ID 返回 PROJECT_EXISTS、列出项目。
- [ ] artifact_service：限制 5 MiB、UTF-8/BOM、CSV schema 和有限数值。
- [ ] 显式核对上传路径项目代码和 CSV project_id 一致。
- [ ] 生成安全 storage_key，文件存 .runtime/artifacts；数据库保存 hash/文件名/行信息。
- [ ] 校验整个文件再事务插入；坏文件不留下部分实验。
- [ ] 相同项目同 hash 重传复用原 artifact，返回 reused 标志。
- [ ] comparison_service：按当前项目查询 artifact，查受控文件路径，调用已有 tools.compare_runs。
- [ ] 正常结果保存 comparison_id、artifact_id、输入 ID、原值、差值、来源行和 hash。
- [ ] ComparisonError 转为统一业务错误；前端展示内容来自真实结果。

本版只比较同一 artifact 的两个 run。不同文件同名 run 先选版本，不自动选“最新”。

**3:00—4:00｜写 API 并先独立调通**

实现架构文档 D2 的六个接口。上传使用 multipart，安装 python-multipart；请求和文件一起时按 FastAPI 的表单机制处理。[文件上传说明](https://fastapi.tiangolo.com/tutorial/request-files/)

```powershell
$rmProjectBody = @{id='P001';name='Synthetic demo';description='合成演示数据'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/projects' -Method Post -ContentType 'application/json' -Body $rmProjectBody
Invoke-RestMethod 'http://127.0.0.1:8000/api/projects'
curl.exe --fail-with-body -F 'file=@examples/runs_demo.csv' 'http://127.0.0.1:8000/api/projects/P001/artifacts'
```

从上传响应复制真实 artifact_id，再比较：

```powershell
$rmArtifactId = '替换为上传响应的artifact_id'
$rmCompareBody = @{artifact_id=$rmArtifactId;baseline_run_id='R001';candidate_run_id='R002'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/projects/P001/comparisons' -Method Post -ContentType 'application/json' -Body $rmCompareBody
```

示例中改善 10% 是合成数据计算结果。把 candidate 改 R003，应返回 INCOMPARABLE_RUNS 与两个差异字段；不能返回成功的排行榜。

**4:00—6:00｜把这些功能接到页面**

```powershell
pnpm -C admin-ui add echarts
```

- [ ] ProjectSidebar：列表、新建、切换；保存 selectedProjectId。
- [ ] ArtifactPanel：文件选择、上传按钮、上传状态、版本列表、实验表格。
- [ ] 比较表单：选 baseline/candidate，显示 artifact 版本。
- [ ] ComparisonCard：指标方向、原值、差值、改善率、来源行；零基线显示“无相对百分比”。
- [ ] 用一个 ECharts 双柱图显示两个原值，销毁组件时释放实例。
- [ ] 切换项目清空旧选项，避免拿旧 artifact 发新请求。
- [ ] 请求中按钮禁用，失败清除不适用的旧结果并展示错误。
- [ ] 刷新后重新读取项目/文件列表，业务数据来自后端。

**6:00—7:00｜针对业务完整性写测试**

- [ ] API 建项、重复项目、上传、实验查询、比较成功。
- [ ] 不同协议、非法 CSV、过大文件、项目不符、artifact 不存在。
- [ ] 文件校验失败后没有部分 ExperimentRun。
- [ ] 同 hash 重传不重复生成实验记录。
- [ ] 原有 14 个基础工具测试仍通过。
- [ ] 数据库测试用独立测试库，测试结束只清理自己的测试记录。

可将这些 API 用例写进 scripts/verify_api.py day02，使用独立项目代码或测试库，重复运行不会撞旧数据。命令约定由你实现：

```powershell
uv run python -X utf8 scripts/verify_api.py day02
uv run python -X utf8 -m pytest -q
pnpm -C admin-ui build
```

**7:00—8:00｜Git、联调与复盘**

分支 feat/day02-data-comparison，PR 说明“导入后可以按版本比较，并拒绝不同口径”。

- [ ] CI 增加 PostgreSQL 测试 service 与迁移步骤；普通 CI 无真实模型 Key。
- [ ] 实际操作 P001 和 P002，确认页面切换与范围检查。
- [ ] 重启 API 和数据库服务，项目与实验仍可读取。
- [ ] 提交迁移、锁文件、前端与测试；看 staged diff 后推送。
- [ ] PR 检查通过再合并。
- [ ] docs/day02.md 保存成功/拒绝两次响应与页面截图，注明合成数据。

当天结束可展示：浏览器新建项目 → 上传 → 对比 R001/R002 → 查看来源 → 尝试 R003 并得到明确拒绝。

