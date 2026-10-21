**Day 7：从干净克隆运行全部首版功能，并发布 v0.1.0**

今天交付可复现的前后端、数据库迁移、worker/beat、测试与 GitHub 发布记录。预算 8 小时。Day 6 的关键失败项优先修复。

**0:00—2:00｜构建完整应用镜像与 Compose**

- [ ] Dockerfile 使用多阶段构建：admin-ui 先构建，Python 运行层带 app/tools/scripts/migrations 与前端 dist。
- [ ] 使用锁文件安装：前端 frozen-lockfile，后端 uv sync --locked --no-dev。
- [ ] 镜像中有 uv 命令，api/worker/beat 使用同一应用镜像。
- [ ] API 托管前端 assets 和根页面，保持 /api 路由；未知 API 不错误返回 index.html。
- [ ] api、worker 共享受控文件卷，STORAGE_DIR 在容器中统一为 /data/artifacts。
- [ ] PostgreSQL 数据有命名卷；Redis 的持久化/重启行为按实际配置记录，业务恢复以 PostgreSQL 为准。
- [ ] DATABASE_URL 容器中使用 postgres 主机，REDIS_URL 使用 redis 主机。
- [ ] .dockerignore 排除 .env、.git、.venv、node_modules、.runtime、缓存、真实数据与模型权重。
- [ ] API 暴露 127.0.0.1:指定端口；worker/beat 无对外端口。
- [ ] API 健康检查验证必要基础依赖，模型 Key 配置状态另列；不在每次健康检查消耗模型 API。
- [ ] 最终镜像和基础镜像版本/摘要写进 docs/environment.md。

Compose 先启动健康的基础服务，再迁移，最后启动消费者。depends_on 不能代替业务迁移。[启动顺序](https://docs.docker.com/compose/how-tos/startup-order/)

```powershell
docker compose config --quiet
docker compose build
docker compose up -d --wait postgres redis
docker compose run --rm --no-deps api uv run alembic upgrade head
docker compose run --rm --no-deps api uv run python scripts/init_checkpointer.py
docker compose up -d api worker beat
docker compose ps
Invoke-RestMethod 'http://127.0.0.1:8000/api/health'
```

scripts/init_checkpointer.py 是你在 D3/D4 实现的幂等初始化入口。镜像必须包含该脚本、Alembic 配置和迁移。上述命令完成后本机访问 http://localhost:8000，应直接看到登录页。

- [ ] 写 scripts/start.ps1，把同一顺序封装起来，检查每条原生命令的退出码，失败停止。
- [ ] 写 scripts/stop.ps1，仅停止服务，默认保留数据。
- [ ] 保留数据库迁移版本和镜像回退说明；不提供一键删数据作为普通修复步骤。

**2:00—3:00｜完成 GitHub Actions 与依赖复现**

CI 至少两类检查：

- [ ] Python：使用锁定 Python 小版本与 uv，uv sync --locked；Ruff 格式/静态检查、pytest；PostgreSQL/Redis service 支持相应数据库测试，先迁移。
- [ ] 前端：按 packageManager 字段安装对应 pnpm，frozen-lockfile 安装、类型检查/构建；配置好的 Playwright 用例执行。
- [ ] 应用镜像至少构建一次，可作为独立 job；构建不需要真实模型 Key。
- [ ] 测试模型模式仅用于 CI/测试配置；真实部署 UI 显示实际模型配置。
- [ ] CI 依赖官方当前维护的 Actions，固定明确版本或提交，不引用任意变化的 main。
- [ ] 失败时输出脱敏错误，上传测试报告；不上传 .env、完整数据库、真实聊天或权重。

参考：[GitHub Python 构建与测试](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)。CI 通过表示 CI 覆盖的用例通过；真实模型、真实队列和干净克隆另有今天的实际验收。

**3:00—4:30｜用全新目录和全新数据卷证明可复现**

- [ ] 把当天发布前代码推到 GitHub；在新的空目录 clone。
- [ ] 若指定目录已存在，另选新目录；不用删除旧目录解决。
- [ ] 新目录只复制 .env.example 为 .env，再由你填真实配置；不复制原项目 .venv/node_modules/.runtime/数据库。
- [ ] .env.example 的 APP_PORT 支持 Compose 外部映射；新副本设置为 8001，避免原服务端口冲突。
- [ ] Compose 不固定 container_name，使用独立 project name，确保是全新数据卷。
- [ ] 新克隆的 README 不依赖本机简历目录或仓库外文件。

```powershell
$rmGithubUser = '替换为你的GitHub用户名'
git clone "https://github.com/$rmGithubUser/ResearchMate.git" 'D:\Study\ResearchMate-repro'
Set-Location -LiteralPath 'D:\Study\ResearchMate-repro'
Copy-Item -LiteralPath '.env.example' -Destination '.env'
```

你编辑好 .env（包括 APP_PORT=8001）后运行：

```powershell
docker compose -p researchmate-repro config --quiet
docker compose -p researchmate-repro build
docker compose -p researchmate-repro up -d --wait postgres redis
docker compose -p researchmate-repro run --rm --no-deps api uv run alembic upgrade head
docker compose -p researchmate-repro run --rm --no-deps api uv run python scripts/init_checkpointer.py
docker compose -p researchmate-repro up -d api worker beat
Invoke-RestMethod 'http://127.0.0.1:8001/api/health'
```

打开 http://localhost:8001，通过页面建项目、导入 examples 数据、对话和提醒。不能仅以容器显示 Up 判定业务可用。

**4:30—5:30｜完整真实演示**

按总验收 C01—C20，特别实际运行：

- [ ] 登录 → 建 P001 → 上传 → R001/R002 比较 → R003 拒绝。
- [ ] 真实模型调用比较工具，并展示来源。
- [ ] 偏好跨新会话读取，修改后生效。
- [ ] 中断选文件 → 重启 → 补充并恢复。
- [ ] 创建 60 秒后提醒 → 到期出现一次通知。
- [ ] 改期/取消/完成待办后停止旧提醒。
- [ ] 暂停 worker → 排队 → 恢复完成，刷新/SSE 重连不重复。
- [ ] 模型服务失败时如实显示，程序结果与状态一致。

记录实际耗时和边界，缺少证据的项保持 NOT_RUN，不写通过。

**5:30—6:30｜补齐交付说明**

README 至少包含：

- [ ] 一句话业务、用户场景、功能截图/短视频。
- [ ] 架构图和 LovAgent 参考来源；自己实现的模块与已有起步工具来源。
- [ ] 前置环境、配置字段、模型要求、启动/停止、迁移和测试命令。
- [ ] 示例数据明确为合成数据，真实研究指标和 Agent 验收结果分开。
- [ ] 当前可用功能与第二阶段范围。
- [ ] 完整目录链接都在仓库内或指向可访问的外部文档。
- [ ] 常见错误：Docker engine、端口、数据库地址、迁移、Key、工具调用能力、Cookie、worker、SSE。
- [ ] 如何备份/恢复数据与回退镜像，数据库 schema 不兼容时怎样处理。

更新 docs/acceptance.md，列出 case_id、环境、版本、实际结果、证据和未覆盖项。

**6:30—8:00｜修复剩余失败、合并与发布**

分支 release/v0.1.0，PR 标题围绕最终行为与实际验证。

- [ ] 本地检查、CI、20 项首版验收都完成；存在核心失败则继续修复，不提前打完成标签。
- [ ] 审阅 staged diff 和 Files changed，确认无真实 Key/私有数据/数据库/权重。
- [ ] 合并发布 PR，更新 main 并记录实际 commit。
- [ ] 打 tag 并推送：

```powershell
git switch main
git pull --ff-only
git tag -a v0.1.0 -m 'ResearchMate v0.1.0'
git push origin v0.1.0
```

- [ ] GitHub Releases 从该 tag 建 Release，写功能、启动方式、实际验证和限制。
- [ ] 如附演示视频，确认来自合成数据、配置页未显示 Key。
- [ ] 最终 docs/day07.md 留 GitHub 仓库/Release/PR/CI 链接，说明独立开发与自审。

交付终点：别人按 README clone、配置 API、启动 Docker 后，可以通过浏览器完成全部 v0.1 业务；代码、迁移、锁文件和验证记录对应同一发布版本。

