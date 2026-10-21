**Day 1：让自己的前后端启动，并完成第一次 GitHub 上传**

**2026-10-21 实际开发入口：[Day 1 逐步实操](./Day01-逐步实操.md)**，配合 [最小代码示例](./Day01-最小代码示例.md)。新版本将 Git 基线提前到写应用之前，具体操作顺序以新版本为准；下文保留当天目标概览。

今天完成：本地环境、API/React 骨架、模型能力预检、Git 仓库与最小 CI。预算 8 小时。今天不开始做完整聊天业务。

**0:00—0:30｜沿 LovAgent 认一次结构**

- [ ] 读 app/main.py：哪些路由注册、前端如何托管、后台入口在哪里。
- [ ] 看 admin-ui/src/api.ts：页面怎样请求后端。
- [ ] 用自己的话写 docs/architecture.md 前半页：浏览器 → API → 服务/图 → 数据。
- [ ] 确认自己的 Git 根目录只能是 ResearchMate，简历和其它研究资料保留在外面。

参考：[LovAgent 应用入口](https://github.com/freecodetiger/lovagent/blob/5fc40146cf10820e9f05cac53b14cd4be9ed6a86/app/main.py)、[前端请求](https://github.com/freecodetiger/lovagent/blob/5fc40146cf10820e9f05cac53b14cd4be9ed6a86/admin-ui/src/api.ts)。今天无需部署企业微信回调。

**0:30—2:00｜检查并补齐环境**

先在你自己打开的 PowerShell 运行：

```powershell
Set-Location -LiteralPath 'D:\Study\简历\ResearchMate'
Get-Command python,node,pnpm,git,docker,uv -ErrorAction SilentlyContinue
python --version
node --version
pnpm --version
git --version
docker compose version
docker version
```

- [ ] 启动 Docker Desktop，选择 Linux containers，等待 docker version 同时显示 Client 和 Server。
- [ ] 缺少 uv 时安装并重新打开终端验证：

```powershell
winget install --id astral-sh.uv -e
uv --version
uv python install 3.12
uv init --bare --python 3.12 --vcs none
uv python pin 3.12
uv add fastapi 'uvicorn[standard]' pydantic-settings httpx langchain-openai
uv add --dev pytest ruff
uv run python --version
uv run python -X utf8 -m pytest tests/test_compare_runs.py -q
```

uv init 在尚无 pyproject.toml 时执行一次。已有该文件时先检查，不重复初始化。uv 管理本项目 .venv，不往你原来的 Anaconda 研究环境升级整套依赖。[uv 安装](https://docs.astral.sh/uv/getting-started/installation/)、[锁定与同步](https://docs.astral.sh/uv/concepts/projects/sync/)

- [ ] 前端 Node/pnpm 若在新终端不可用，安装到你可长期使用的环境，记录实际路径与版本。
- [ ] 当前 Vite 要求 Node 20.19+ 或 22.12+，模板的 engines 也要满足；已有 Node 24.19.0 仍要通过安装和构建验证。[Vite 入门](https://vite.dev/guide/)
- [ ] 创建 docker-compose.yml，先只定义 postgres、redis；开发端口绑定 127.0.0.1，配置健康检查与命名数据卷。
- [ ] 记录基础镜像明确版本；未来改版本需重做验证，Day 7 固定验收使用的镜像/摘要。

```powershell
docker compose config --quiet
docker compose up -d postgres redis
docker compose ps
docker compose exec postgres pg_isready -U researchmate -d researchmate
docker compose exec redis redis-cli ping
```

这里的用户名和库名要求与你编写的 Compose 一致。Redis 期待 PONG；PostgreSQL 期待 accepting connections。正常停止用 docker compose stop，不使用 down -v 清空数据库。

**2:00—3:00｜亲手写后端骨架**

- [ ] 创建 app/__init__.py、main.py、config.py、routers/health.py。
- [ ] Settings 从根目录 .env 读取并验证配置，创建时机可控，方便测试替换。
- [ ] 写 GET /api/health，返回真实版本与状态。
- [ ] 写 GET /api/settings/status，只返回配置是否齐全、模型名、Base URL 主机；不返回 Key。
- [ ] 写一个 API 测试：TestClient 能检查两个接口，缺配置有明确状态。
- [ ] .env.example 只含示例；真实配置写 .env。

配置约定：

```dotenv
APP_ENV=development
DATABASE_URL=postgresql+psycopg://researchmate:local-dev-password@localhost:5432/researchmate
REDIS_URL=redis://localhost:6379/0
MODEL_BASE_URL=https://replace-with-your-provider.example/v1
MODEL_NAME=replace-with-your-model
MODEL_API_KEY=replace_me
ADMIN_PASSWORD=replace_with_local_password
SESSION_SECRET=replace_with_random_local_secret
APP_TIMEZONE=Asia/Shanghai
STORAGE_DIR=.runtime/artifacts
```

示例 URL 不可用于连通性测试，需要替换为你自己的服务配置。前端只能得到非敏感配置状态。

```powershell
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

新开终端：

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/health'
```

**3:00—4:00｜亲手写前端骨架**

```powershell
pnpm create vite admin-ui --template react-ts
pnpm -C admin-ui install
pnpm -C admin-ui dev
```

仅在 admin-ui 尚未创建时运行脚手架命令。

- [ ] vite.config.ts 把 /api 代理到 http://127.0.0.1:8000。
- [ ] src/api.ts 统一 fetch、错误提取、credentials: include。
- [ ] App.tsx 调真实 /api/health 和 /api/settings/status，显示成功/失败状态。
- [ ] styles.css 做左侧项目栏、中间工作区、右侧详情的基础布局，窄屏可滚动或折叠。
- [ ] 创建 types.ts，先写 HealthResponse 和 SettingsStatus。
- [ ] 页面暂时只显示已能操作的入口，后续按天增加组件。
- [ ] 浏览器 Network 能看到 /api/health，关掉后端后页面显示连接失败。

**4:00—5:00｜模型预检尽早排除阻塞**

- [ ] 写 app/providers/model_provider.py，统一根据 Settings 创建聊天模型。
- [ ] 写 scripts/check_llm.py，读真实 .env，先请求简短回复，再绑定一个无副作用的演示工具检查 tool_calls。
- [ ] 输出仅含配置状态、模型名、是否生成回复、工具名与参数、耗时；不打印 Authorization/Key。
- [ ] 实际运行一次，确认能得到合法工具调用；仅有聊天能力时更换支持工具的模型配置后重测。
- [ ] API 不可用时保留具体错误，不用固定文本伪装模型成功。

```powershell
uv run python -X utf8 -m scripts.check_llm
```

**5:00—6:30｜Git 与 GitHub 从今天开始**

完整步骤见 [Git 手册](./Git与GitHub操作手册.md)。

- [ ] 补 .gitignore：.env、.env.*、!.env.example、.venv、.runtime、node_modules、dist、缓存、logs、测试截图；保留 examples。
- [ ] GitHub 创建空的 ResearchMate 仓库；记下真实 HTTPS 地址。
- [ ] 本地初始化 main，首次只提交已有设计/示例/基础工具与忽略规则，再推 main。
- [ ] 创建 feat/day01-bootstrap；将今天的前后端/环境/预检代码提交在此分支。
- [ ] 写 .github/workflows/ci.yml：uv sync --locked、Ruff、现有 pytest、前端 frozen-lockfile 安装与构建。
- [ ] uv.lock、pnpm-lock.yaml、.python-version 进入 Git；.env 不进入。
- [ ] 推功能分支，GitHub 开 PR，检查 Files changed 与 CI，合并。

**6:30—8:00｜验收、修复、记录**

```powershell
uv run ruff format .
uv run ruff check .
uv run python -X utf8 -m pytest -q
pnpm -C admin-ui build
git status
```

- [ ] Python 测试通过，前端构建通过。
- [ ] 浏览器看得到真实后端健康状态。
- [ ] 模型预检有实际结果，Key 未出现在日志/Git diff。
- [ ] PostgreSQL、Redis 正常启动。
- [ ] GitHub 能看到代码、PR 与 CI 结果。
- [ ] docs/day01.md 记录版本、命令、结果、错误与剩余项。
- [ ] 最后解释：页面、HTTP API、模型服务、数据库各解决什么问题。

当天结束可展示：打开自己的页面 → 显示 API 正常 → 查看配置状态 → 展示 GitHub 当天 PR。未通过的基础环节优先修复，不先增加复杂页面。

