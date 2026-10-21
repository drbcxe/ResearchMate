**Day 1 逐步实操：2026-10-21**

按每天约 8 小时安排。今天的目标：你的页面通过真实 HTTP 调用自己的后端，基础服务可用，真实模型预检有结果，代码已经通过 Git 上传 GitHub。

目前核查：ResearchMate 尚无 pyproject.toml、app、admin-ui 和 Git 仓库；当前终端未找到 uv，Docker Linux engine 未启动。本次只补充教学材料，不替你安装环境、创建应用或提交代码。

今天以本文的操作顺序为准。先自己按照任务描述编写；卡住时对照 [最小代码示例](./Day01-最小代码示例.md)，每个示例只服务今天的基础链路。

**一、先知道今天最后应该有什么**

- [ ] http://localhost:5173 显示 ResearchMate 页面。
- [ ] 页面显示后端健康状态和模型配置状态，数据来自 /api。
- [ ] http://127.0.0.1:8000/docs 可以调接口。
- [ ] PostgreSQL 接受连接，Redis 返回 PONG。
- [ ] 模型预检能得到真实回复和合法工具调用。
- [ ] 原比较工具测试和新增 API 测试通过，前端构建通过。
- [ ] GitHub 中有 main、Day 1 功能 PR 和成功 CI。
- [ ] docs/day01.md 记录实际结果。

今天所有终端从项目根目录开始，除非步骤明确切换：

```powershell
Set-Location -LiteralPath 'D:\Study\简历\ResearchMate'
Get-Location
```

建议保留三个终端标签：A 跑后端，B 跑前端，C 运行检查/Git。常驻服务窗口显示日志是正常行为；Ctrl+C 停止当前服务。

**二、0:00—0:20：看懂一条最短架构**

只读两个参考文件：

- [LovAgent app/main.py](https://github.com/freecodetiger/lovagent/blob/5fc40146cf10820e9f05cac53b14cd4be9ed6a86/app/main.py)：应用在哪里创建，路由怎样注册。
- [LovAgent admin-ui/src/api.ts](https://github.com/freecodetiger/lovagent/blob/5fc40146cf10820e9f05cac53b14cd4be9ed6a86/admin-ui/src/api.ts)：前端如何请求、如何处理失败。

写下三句话：

1. 浏览器显示什么？
2. FastAPI 提供什么？
3. 模型、数据库与 Web 服务为什么分开？

把自己的回答保存为 docs/architecture.md。此时只需半页，不通读整个仓库。

**三、0:20—1:30：检查环境，建立独立 Python 项目**

先运行，缺什么再装什么：

```powershell
Get-Command python,node,pnpm,git,docker,uv -ErrorAction SilentlyContinue
python --version
node --version
pnpm --version
git --version
docker compose version
docker version
```

判断标准：

| 工具 | 你要看到什么 |
|---|---|
| Git | 输出版本号 |
| Node/pnpm | 都能找到并输出版本，前端安装不报 engines 错误 |
| uv | 能输出版本号 |
| Docker | 同时有 Client、Server，能连接 Linux engine |

缺少 uv：

```powershell
winget install --id astral-sh.uv -e
```

安装完成后新开终端，再执行 uv --version。该命令来自 [uv 官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)。

Node/pnpm 在你自己的终端找不到时，先安装受维护的 Node LTS，再按 [pnpm 官方安装说明](https://pnpm.io/installation)安装；本手册示例使用已观察到的 pnpm 11.25.0。已有 pnpm 时先用现有版本，不重复覆盖。

打开 Docker Desktop，等待 Linux engine 启动。只安装 Docker CLI 还不能运行容器。若 Desktop 报 WSL/虚拟化错误，按其实际错误处理；不要继续启动 Compose 来掩盖未启动的引擎。

环境通过后，在项目根目录逐行执行：

```powershell
uv python install 3.12
uv init --bare --python 3.12 --vcs none
uv python pin 3.12
uv add fastapi 'uvicorn[standard]' pydantic-settings httpx langchain-openai
uv add --dev pytest ruff
uv run python --version
uv run python -X utf8 -m pytest tests/test_compare_runs.py -q
```

仅在 pyproject.toml 尚不存在时运行 init；--vcs none 让你稍后自己学习 Git 初始化。安装依赖时会生成 .venv、pyproject.toml 和 uv.lock。uv run 使用项目环境，不需要先 conda activate 或手动 activate。

验收：

- [ ] uv run python 使用本项目环境。
- [ ] 现有比较工具 14 个测试通过。
- [ ] pyproject.toml、uv.lock、.python-version 可见。
- [ ] 你能解释声明依赖与锁文件的区别。

**四、1:30—2:00：先建立 Git 基线和功能分支**

先补 .gitignore，保留已有规则并增加：

```gitignore
.env
.env.*
!.env.example
.venv/
.runtime/
node_modules/
dist/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
*.log
```

然后按 [Git 操作手册](./Git与GitHub操作手册.md)完成：

1. 在 ResearchMate 内 git init -b main。
2. 配置自己的提交姓名/邮箱。
3. 提交已存在的方案、示例、基础工具和忽略规则作为基线。
4. GitHub 网页创建空 ResearchMate 仓库。
5. 设置 origin，第一次 push main。
6. 创建 feat/day01-bootstrap，在此分支写今天的新功能。

```powershell
git init -b main
git config user.name '替换为你的提交姓名'
git config user.email '替换为你的提交邮箱'
git add -- .gitignore README.md tools tests examples evals '工具与状态契约.md' '开发关卡.md' '验证记录.md' '7天开发清单'
git diff --cached --stat
git diff --cached
git commit -m 'chore: record ResearchMate starting baseline'
```

新建远程仓库后，把地址换成自己的：

```powershell
$rmGithubUser = '替换为你的GitHub用户名'
git remote add origin "https://github.com/$rmGithubUser/ResearchMate.git"
git push -u origin main
git switch -c feat/day01-bootstrap
```

前一步安装生成的依赖文件暂不进入基线提交，它们随功能分支的前后端代码一起提交。不要在 D:\Study\简历 初始化仓库；Git 根目录应为 ResearchMate。

**五、2:00—3:15：亲手写两个后端接口**

创建以下目录和文件；Python 包目录中的 __init__.py 可以为空：

```text
app/
  __init__.py
  main.py
  config.py
  routers/
    __init__.py
    health.py
  providers/
    __init__.py
scripts/
  __init__.py
tests/
  test_health_api.py
```

逐个实现：

| 文件 | 你要写的职责 |
|---|---|
| config.py | Settings 从 .env 读取模型配置，get_settings 管理初始化 |
| routers/health.py | 两个 GET 路由，读取 Settings，返回脱敏状态 |
| main.py | 创建 FastAPI app，注册 /api 路由 |
| test_health_api.py | 验证健康响应、缺配置与 Key 不出现在响应中 |

今天接口契约固定：

```json
GET /api/health
{"status":"ok","version":"0.1.0"}

GET /api/settings/status
{"model_configured":false,"model_name":"","base_url_host":""}
```

第二个接口表示配置是否齐全，不表示 API 已经连通。连通性在稍后的预检中实际调用验证。

先创建 .env.example，再复制为 .env；示例中模型字段留空：

```dotenv
APP_ENV=development
DATABASE_URL=postgresql+psycopg://researchmate:local-dev-password@localhost:5432/researchmate
REDIS_URL=redis://localhost:6379/0
MODEL_BASE_URL=
MODEL_NAME=
MODEL_API_KEY=
ADMIN_PASSWORD=
SESSION_SECRET=
APP_TIMEZONE=Asia/Shanghai
STORAGE_DIR=.runtime/artifacts
```

```powershell
Copy-Item -LiteralPath '.env.example' -Destination '.env'
```

只在 .env 尚未创建时复制，已有真实配置时直接编辑。今天无需让 API 连接数据库；不要把“进程启动”误写为“数据库检查已通过”。

在终端 A 启动：

```powershell
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

终端 C 验证：

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/health'
Invoke-RestMethod 'http://127.0.0.1:8000/api/settings/status'
```

再打开 http://127.0.0.1:8000/docs，点击接口 → Try it out → Execute，观察 JSON。

检查：修改代码后 reload 能重新加载；缺模型 Key 时健康接口仍可访问，配置接口返回 false。

**六、3:15—4:15：创建前端，并接真实 API**

admin-ui 尚不存在时运行：

```powershell
pnpm create vite admin-ui --template react-ts
pnpm -C admin-ui install
```

根据当前 pnpm --version，在 admin-ui/package.json 添加准确的 packageManager 字段，例如 pnpm@11.25.0，CI 使用同版本。

你要修改五个位置：

1. vite.config.ts：/api 代理到 http://127.0.0.1:8000，固定 5173 且 strictPort。
2. src/types.ts：定义 HealthResponse、SettingsStatus。
3. src/api.ts：getJson 统一请求与错误处理。
4. src/App.tsx：调用两个 API，显示数据、加载状态与失败。
5. src/index.css：替换脚手架默认布局，完成最小左右分栏；App.tsx 不再引入默认 App.css。

在终端 B 运行：

```powershell
pnpm -C admin-ui dev
```

打开 http://localhost:5173，按 F12 查看 Network：

- [ ] 看到 /api/health 和 /api/settings/status。
- [ ] 响应和终端直接访问 API 的内容一致。
- [ ] 关闭终端 A 的后端，刷新状态后页面显示请求失败。
- [ ] 重启后端，再刷新能恢复。
- [ ] 页面没有 API Key。

使用 /api 相对路径配合 Vite 代理，开发阶段先不扩大跨域权限。[Vite 代理配置](https://vite.dev/config/server-options.html#server-proxy)

**七、4:15—5:00：启动 PostgreSQL 和 Redis**

在根目录创建 docker-compose.yml，先只定义 postgres、redis。可对照 [最小示例中的 Compose](./Day01-最小代码示例.md)。

本例固定 PostgreSQL 18.6-bookworm 和 Redis 8.10.2-alpine，镜像标签已在官方列表核对；本机实际拉取/启动由你验证并记录。PostgreSQL 18 的卷挂载路径为 /var/lib/postgresql。[PostgreSQL 镜像说明](https://hub.docker.com/_/postgres)、[Redis 镜像说明](https://hub.docker.com/_/redis)

```powershell
docker compose config --quiet
docker compose up -d --wait postgres redis
docker compose ps
docker compose exec postgres pg_isready -U researchmate -d researchmate
docker compose exec redis redis-cli ping
```

期待 PostgreSQL 显示 accepting connections，Redis 显示 PONG，两个容器 healthy。

端口被占用时先查实际占用者；确需改映射时同步 .env。正常收工用 docker compose stop，保留卷。今天不需要数据库表和 ORM，它们在 Day 2 接入。

**八、5:00—6:00：验证真实模型和工具调用**

准备三项信息：模型名、Base URL、API Key。写入本机 .env，不发到聊天或 GitHub。

创建 app/providers/model_provider.py、scripts/check_llm.py：

1. get_chat_model(settings) 统一初始化模型客户端。
2. 先发一个简单文本请求。
3. 定义无副作用的 add_numbers(a,b)，绑定给模型。
4. 要求模型用这个工具计算 2+3。
5. 检查是否收到合法 tool_call，按其参数在 Python 中执行。
6. 输出配置名、是否返回回复、工具名、参数、结果和耗时，不输出 Key。

运行模块：

```powershell
uv run python -X utf8 -m scripts.check_llm
```

用 -m 是为了从项目根目录正确导入 app。scripts 需要 __init__.py；直接运行 scripts/check_llm.py 容易因导入路径配置而失败。

验收示例：

```json
{"chat_ok":true,"tool_call_received":true,"tool_name":"add_numbers","tool_result":5}
```

没有 tool_call 时先核对 Prompt、模型能力与接口兼容性，单次未选工具不能证明模型完全不支持。401 核对 Key，404 核对 Base URL/接口，429 检查限流或配额；错误保持真实，不用固定回复冒充调用成功。

今天只检验模型和工具请求/本地执行，完整 Agent 工具循环在 Day 3 实现。[LangChain 工具绑定](https://docs.langchain.com/oss/python/integrations/chat/openai#bind-tools)

**九、6:00—7:00：自动检查与最小 CI**

先补三条 API 测试：健康返回正确；缺模型配置为 false；配置存在时响应不泄漏 Key。测试通过依赖注入使用测试 Settings，不请求真实模型，也不读取真实 .env。

```powershell
uv run ruff format .
uv run ruff check .
uv run python -X utf8 -m pytest -q
pnpm -C admin-ui build
```

以上都是要通过的检查。若现有基础工具被格式化，只保留行为不变的改动并重跑测试。

编写 .github/workflows/ci.yml，步骤和本地一致：

- checkout；
- 安装 uv/Python，uv sync --locked；
- Ruff 与 pytest；
- 安装 Node 与匹配 pnpm；
- frozen-lockfile 安装与前端 build。

[最小示例](./Day01-最小代码示例.md)提供了 YAML 参考。CI 不需要你的模型 Key。当前参考 Actions/uv 标签核查日期是 2026-10-21；若后续更换，记录实际版本再验证。

**十、7:00—8:00：提交、PR、验收与记录**

确认 .env 被忽略，再提交今天实现：

```powershell
git status --short
git check-ignore .env
git add -- app admin-ui scripts tests .github docker-compose.yml .env.example pyproject.toml uv.lock .python-version .gitignore docs
git diff --cached --stat
git diff --cached
git commit -m 'feat: bootstrap frontend backend and model preflight'
git push -u origin feat/day01-bootstrap
```

命令中的路径需要今天都已创建；缺少时先确认原因，只暂存真实完成的文件。

GitHub 网页：

1. 打开仓库，选择 Compare & pull request。
2. base 为 main，compare 为 feat/day01-bootstrap。
3. 写清新增两个接口、前端、基础服务、模型预检及真实验证结果。
4. 自审 Files changed；查看 Checks，失败修复后继续推同一分支。
5. 检查通过后合并，注明独立开发/自审。
6. 本地更新：

```powershell
git switch main
git pull --ff-only
git log --oneline -5
```

docs/day01.md 记录：实际环境版本、启动命令、测试结果、模型预检摘要、一个错误及处理、PR/CI 链接。使用 [每日记录模板](./每日记录模板.md)，不预写通过。

**十一、收工验收**

- [ ] 页面可打开，显示真实 API 数据。
- [ ] 停后端后页面能显示错误，重启后恢复。
- [ ] 两个基础容器 healthy，ping 检查通过。
- [ ] 模型真实回复和工具调用有可核对结果。
- [ ] 测试与前端构建通过。
- [ ] GitHub 中有今天的功能代码和 PR，CI 通过。
- [ ] 没有上传真实 .env、数据卷或研究权重。

最后自己回答五个问题：uv.lock 为什么提交？/api 请求怎样到达8000？配置齐全与模型连通有什么区别？tool_call 是谁执行的？为什么 PostgreSQL 容器启动不代表业务表已经创建？

如果环境步骤卡住，先保存完整错误并解决该步；今天的进度按实际勾选，不提前把后续项算完成。

