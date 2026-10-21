**Day 1 最小代码示例：先理解，再亲手实现**

本文件配合 [逐步实操](./Day01-逐步实操.md) 使用。代码块中的路径是你要创建的目标，示例仍保存在教学 Markdown 内，本次没有替你生成 app、admin-ui 或真实 .env。

先按任务描述自己尝试；需要对照时一次只看一个文件。运行后能解释每段代码的输入、输出和调用关系，再进入下一步。下列 Python、TS、YAML 示例使用 Day 1 的依赖和契约；完整 Agent 在 Day 3 接入。

**一、后端配置：app/config.py**

你要理解：配置从环境读取；配置状态和模型连通性分开；Key 不参与接口输出；应用每次启动读取一次配置。

```python
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    model_base_url: str = ""
    model_name: str = ""
    model_api_key: SecretStr = SecretStr("")

    @property
    def base_url_host(self) -> str:
        try:
            parsed = urlsplit(self.model_base_url.strip())
            if parsed.scheme not in {"http", "https"}:
                return ""
            if parsed.username or parsed.password:
                return ""
            return parsed.hostname or ""
        except ValueError:
            return ""

    @property
    def model_configured(self) -> bool:
        key = self.model_api_key.get_secret_value().strip()
        return bool(
            self.base_url_host
            and self.model_name.strip()
            and key
            and key != "replace_me"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- BaseSettings 将 MODEL_NAME 等环境变量映射到字段；正常环境变量会覆盖 .env。
- extra="ignore" 让今天没使用的数据库等配置留到后续使用；新增必需字段时还要明确校验。
- SecretStr 减少普通 repr 时暴露 Key 的机会，但程序仍能主动取出值，不能代替输出边界。
- lru_cache 避免每个请求重新加载 .env。你修改 .env 后，停止并重新启动后端才会加载新值；刷新页面不会清掉这个缓存。
- base_url_host 只用于展示主机，配置检查只是基础格式和齐全性检查，真实能力仍由预检验证。

[Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

**二、路由：app/routers/health.py**

app/routers/__init__.py 创建为空文件。

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


class SettingsStatus(BaseModel):
    model_configured: bool
    model_name: str
    base_url_host: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/settings/status", response_model=SettingsStatus)
def settings_status(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SettingsStatus:
    return SettingsStatus(
        model_configured=settings.model_configured,
        model_name=settings.model_name,
        base_url_host=settings.base_url_host,
    )
```

你要解释：Depends 怎样让路由拿到 Settings？为什么直接 return settings.model_dump() 不合适？

这里 /health 只表示当前 API 进程能够响应。今天的 PostgreSQL/Redis 验证独立执行；Day 2 再为必要依赖加就绪检查。

**三、应用入口：app/main.py**

app/__init__.py 创建为空文件。

```python
from fastapi import FastAPI

from app.routers.health import router as health_router

app = FastAPI(title="ResearchMate", version="0.1.0")
app.include_router(health_router, prefix="/api")
```

启动 uvicorn app.main:app 的含义：导入 app/main.py，使用其中名为 app 的 FastAPI 实例。外层 app 目录与内层 app 变量是两件事。

**四、API 测试：tests/test_health_api.py**

这些测试有明确业务目的：检查缺配置仍可访问，以及 Key 不进入公开响应。使用依赖替换，不读你的真实 .env，不请求任何模型服务。

```python
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


@pytest.fixture
def client():
    settings = Settings(
        _env_file=None,
        app_env="test",
        model_base_url="",
        model_name="",
        model_api_key="",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_health_returns_process_status(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_missing_model_configuration_is_reported(client):
    response = client.get("/api/settings/status")
    assert response.status_code == 200
    assert response.json() == {
        "model_configured": False,
        "model_name": "",
        "base_url_host": "",
    }


def test_configuration_response_excludes_api_key(client):
    settings = Settings(
        _env_file=None,
        model_base_url="https://api.example.com/v1",
        model_name="test-model",
        model_api_key="test-key-never-return-this",
    )
    app.dependency_overrides[get_settings] = lambda: settings

    response = client.get("/api/settings/status")

    assert response.status_code == 200
    assert response.json() == {
        "model_configured": True,
        "model_name": "test-model",
        "base_url_host": "api.example.com",
    }
    assert "test-key-never-return-this" not in response.text
    assert "model_api_key" not in response.text
```

写完后运行 uv run python -X utf8 -m pytest -q。今天没有更改原工具用例时，预期原 14 个加新 3 个共 17 个；以你实际运行结果为准。

**五、前端代理：admin-ui/vite.config.ts**

先用 Vite 创建 react-ts 项目，再修改它生成的配置；不要删掉其它必要文件。

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "localhost",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
```

浏览器请求 http://localhost:5173/api/health，Vite 转给 8000。开发代码不写死浏览器要访问的后端端口，后续生产部署仍能保留 /api 路径。

strictPort 的目的是端口已占用时明确失败，避免后台自动换成 5174 而你仍打开旧地址。

[Vite server.proxy](https://vite.dev/config/server-options.html#server-proxy)

**六、前端类型：admin-ui/src/types.ts**

```typescript
export interface HealthResponse {
  status: string;
  version: string;
}

export interface SettingsStatus {
  model_configured: boolean;
  model_name: string;
  base_url_host: string;
}
```

字段名与你的后端响应保持一致。TypeScript 类型帮助开发阶段检查；它不会自动验证服务器返回值，后续复杂数据还需要边界校验。

**七、请求封装：admin-ui/src/api.ts**

```typescript
import type { HealthResponse, SettingsStatus } from "./types";

type ErrorBody = {
  error?: { message?: string };
  detail?: unknown;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    signal: AbortSignal.timeout(10_000),
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ErrorBody | null;
    const detail = typeof body?.detail === "string" ? body.detail : undefined;
    throw new Error(
      body?.error?.message ?? detail ?? `请求失败：HTTP ${response.status}`,
    );
  }

  return (await response.json()) as T;
}

export const api = {
  health: () => getJson<HealthResponse>("/api/health"),
  settingsStatus: () => getJson<SettingsStatus>("/api/settings/status"),
};
```

- credentials 为后续会话 Cookie 留好接口，今天尚未实现登录。
- 超时是请求失败，不表示后端任务已经取消。
- 失败时提取错误信息，不把任意原始响应直接作为 HTML 渲染。

**八、界面：admin-ui/src/App.tsx**

```tsx
import { useCallback, useEffect, useState } from "react";

import { api } from "./api";
import type { HealthResponse, SettingsStatus } from "./types";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [settings, setSettings] = useState<SettingsStatus | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [nextHealth, nextSettings] = await Promise.all([
        api.health(),
        api.settingsStatus(),
      ]);
      setHealth(nextHealth);
      setSettings(nextSettings);
    } catch (cause) {
      setHealth(null);
      setSettings(null);
      setError(cause instanceof Error ? cause.message : "无法读取服务状态");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div className="workspace">
      <aside className="sidebar">
        <p className="eyebrow">RESEARCHMATE</p>
        <h1>研伴</h1>
        <p>科研项目协作助手</p>
        <p className="muted">Day 1 · 服务连接</p>
      </aside>

      <main>
        <header className="page-header">
          <div>
            <h2>开发工作台</h2>
            <p className="muted">检查前端、后端和模型配置是否连通。</p>
          </div>
          <button disabled={loading} onClick={() => void refresh()}>
            {loading ? "检查中…" : "刷新状态"}
          </button>
        </header>

        {error && <p role="alert" className="error">{error}</p>}

        <section className="card" aria-labelledby="api-heading">
          <h3 id="api-heading">后端服务</h3>
          <dl>
            <dt>状态</dt>
            <dd>{health?.status ?? "尚未读取"}</dd>
            <dt>版本</dt>
            <dd>{health?.version ?? "—"}</dd>
          </dl>
        </section>

        <section className="card" aria-labelledby="model-heading">
          <h3 id="model-heading">模型配置</h3>
          <dl>
            <dt>配置是否齐全</dt>
            <dd>
              {settings ? (settings.model_configured ? "已配置" : "未配置") : "尚未读取"}
            </dd>
            <dt>模型名</dt>
            <dd>{settings?.model_name || "—"}</dd>
            <dt>服务主机</dt>
            <dd>{settings?.base_url_host || "—"}</dd>
          </dl>
          <p className="muted">实际调用能力使用本地模型预检命令验证。</p>
        </section>
      </main>
    </div>
  );
}

export default App;
```

不要再 import 默认 App.css；保留脚手架 main.tsx 对 index.css 的导入。React StrictMode 在开发环境可能让首次 GET 发生两次；它不是两次真实写入，也不需要为今天的 GET 去除 StrictMode。

**九、最小样式：admin-ui/src/index.css**

替换原脚手架样式，避免其居中布局覆盖自己的工作台。

```css
:root {
  font-family: system-ui, "Microsoft YaHei", sans-serif;
  color: #253139;
  background: #f4f6f7;
  font-synthesis: none;
  line-height: 1.6;
}

* { box-sizing: border-box; }
body { margin: 0; }
button { font: inherit; }
.workspace { min-height: 100vh; display: grid; grid-template-columns: 240px 1fr; }
.sidebar { padding: 32px 24px; background: #183d3b; color: white; }
.eyebrow { letter-spacing: 0.16em; font-size: 12px; }
.sidebar .muted { color: #b8cfcc; }
main { width: min(100%, 1120px); padding: 40px; }
.page-header { display: flex; align-items: center; justify-content: space-between; gap: 24px; }
h1, h2, h3 { margin-top: 0; }
.muted { color: #687980; font-size: 14px; }
.card { margin-top: 24px; padding: 24px; border: 1px solid #dce3e6; border-radius: 12px; background: white; }
dl { display: grid; grid-template-columns: 160px 1fr; gap: 10px 16px; }
dt { color: #687980; }
dd { margin: 0; overflow-wrap: anywhere; }
button { border: 0; border-radius: 8px; padding: 10px 16px; color: white; background: #24645d; cursor: pointer; }
button:disabled { opacity: 0.6; cursor: wait; }
button:focus-visible { outline: 3px solid #bd973f; outline-offset: 3px; }
.error { padding: 14px 18px; border-radius: 8px; background: #fff0ef; color: #a33127; }

@media (max-width: 720px) {
  .workspace { grid-template-columns: 1fr; }
  .sidebar { padding: 20px; }
  main { padding: 24px 16px; }
  .page-header { align-items: flex-start; flex-direction: column; }
  dl { grid-template-columns: 1fr; gap: 4px; }
  dd { margin-bottom: 10px; }
}
```

今天只实现可查看、可刷新的状态界面。项目管理、聊天框、记忆、提醒按后续每日计划加入，不放不能操作的按钮。

**十、基础服务：docker-compose.yml**

在项目根目录创建：

```yaml
services:
  postgres:
    image: postgres:18.6-bookworm
    environment:
      POSTGRES_DB: researchmate
      POSTGRES_USER: researchmate
      POSTGRES_PASSWORD: local-dev-password
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U researchmate -d researchmate"]
      interval: 5s
      timeout: 5s
      retries: 12

  redis:
    image: redis:8.10.2-alpine
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 12

volumes:
  postgres_data:
  redis_data:
```

这是本地开发配置，与 .env.example 中的数据库账号/口令一致；普通启动不删除卷。PostgreSQL 18 的路径用 /var/lib/postgresql；若选择其它大版本，要核对相应官方镜像说明，不能仅换 tag 不检查路径。

实际运行后记录 image tag 和 repo digest，后续 Docker 部署使用同一验证组合。[PostgreSQL 官方镜像](https://hub.docker.com/_/postgres)、[Redis 官方镜像](https://hub.docker.com/_/redis)

**十一、模型客户端：app/providers/model_provider.py**

app/providers/__init__.py 创建为空文件。

```python
from langchain_openai import ChatOpenAI

from app.config import Settings


def get_chat_model(settings: Settings) -> ChatOpenAI:
    if not settings.model_configured:
        raise ValueError("模型配置缺失或基础格式不正确")

    return ChatOpenAI(
        model=settings.model_name.strip(),
        base_url=settings.model_base_url.strip(),
        api_key=settings.model_api_key.get_secret_value().strip(),
        timeout=30,
        max_retries=1,
        stream_usage=False,
    )
```

本例选择 ChatOpenAI 作为 OpenAI-compatible 文本/工具客户端，只验证你的服务实际支持的基础接口。不同供应商特有能力需要对应适配，不能据“兼容”推断所有能力相同。没有固定 temperature 等可选参数，避免给不支持的模型发送多余配置。

客户端只在预检脚本实际调用时初始化，健康接口不依赖模型可用。

**十二、模型预检：scripts/check_llm.py**

scripts/__init__.py 创建为空文件。这个演示工具只做整数加法，不读取文件，也不连接其它服务。

```python
import json
from time import perf_counter

from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.providers.model_provider import get_chat_model


class AddNumbersInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    a: int = Field(ge=-1000, le=1000)
    b: int = Field(ge=-1000, le=1000)


@tool(args_schema=AddNumbersInput)
def add_numbers(a: int, b: int) -> int:
    """计算两个整数的和；需要精确加法时使用。"""
    return a + b


class PreflightError(ValueError):
    pass


def main() -> int:
    started = perf_counter()
    summary = {
        "chat_ok": False,
        "tool_call_received": False,
        "tool_validated": False,
        "tool_executed": False,
    }

    try:
        settings = get_settings()
        summary["model_name"] = settings.model_name
        model = get_chat_model(settings)

        message = model.invoke("请用一句话说明你已收到这条连接测试。")
        if not message.content:
            raise PreflightError("CHAT_RESPONSE_EMPTY")
        summary["chat_ok"] = True

        response = model.bind_tools([add_numbers]).invoke(
            "请调用 add_numbers 工具计算 2+3。请发出工具调用，不要直接口算。"
        )
        calls = response.tool_calls
        summary["tool_call_received"] = bool(calls)

        if len(calls) != 1:
            raise PreflightError("EXPECTED_ONE_TOOL_CALL")
        call = calls[0]
        if call["name"] != "add_numbers":
            raise PreflightError("UNEXPECTED_TOOL")

        args = AddNumbersInput.model_validate(call["args"])
        if (args.a, args.b) != (2, 3):
            raise PreflightError("UNEXPECTED_TOOL_ARGUMENTS")

        summary["tool_validated"] = True
        summary["tool_name"] = call["name"]
        summary["tool_args"] = args.model_dump()
        summary["tool_result"] = add_numbers.invoke(args.model_dump())
        summary["tool_executed"] = True
        summary["elapsed_seconds"] = round(perf_counter() - started, 2)
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    except Exception as exc:
        summary["elapsed_seconds"] = round(perf_counter() - started, 2)
        summary["error_type"] = type(exc).__name__
        if isinstance(exc, PreflightError):
            summary["error_code"] = str(exc)

        status = getattr(exc, "status_code", None)
        if isinstance(status, int):
            summary["http_status"] = status

        print(json.dumps(summary, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

从根目录运行 uv run python -X utf8 -m scripts.check_llm。它会发起两个真实模型请求，是否收费/使用额度取决于你的模型服务配置。

这里故意不直接打印原始异常、客户端配置和任意模型回复，以免它们包含敏感信息；预检失败保留 HTTP 状态、错误种类和已完成阶段。定位时先按这些字段检查配置，需要更深日志时也只提取脱敏摘要。

执行工具是 add_numbers.invoke(...) 这一行。模型返回的是调用建议与参数，Python 完成校验和执行；向模型回送工具结果并继续生成在 Day 3 接入。

[LangChain 模型客户端与工具绑定](https://docs.langchain.com/oss/python/integrations/chat/openai)

**十三、最小 CI：.github/workflows/ci.yml**

这个例子使用 2026-10-21 已核对的 release 标签：checkout v7.0.1、setup-uv v10.3.0、setup-node v7.1.0、uv 0.13.4。它们与本机实际工具版本可能不同；实施时记录实际组合。长期维护可把 Actions 固定为对应提交 SHA。

pnpm 11.25.0 来自当前环境观察；若你自己终端是另一版本，将 packageManager 与 CI 中版本一起改成同一个已验证值。Node 使用当前已观察到的 24.19.0，仍以实际前端构建通过为验收。

```yaml
name: CI

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.1

      - uses: astral-sh/setup-uv@v10.3.0
        with:
          version: "0.13.4"
          python-version: "3.12"

      - name: Install Python dependencies
        run: uv sync --locked

      - name: Check Python formatting
        run: uv run ruff format --check .

      - name: Check Python code
        run: uv run ruff check .

      - name: Test Python
        run: uv run python -X utf8 -m pytest -q

      - uses: actions/setup-node@v7.1.0
        with:
          node-version: "24.19.0"

      - name: Install pnpm
        run: npm install --global pnpm@11.25.0

      - name: Install frontend dependencies
        run: pnpm -C admin-ui install --frozen-lockfile

      - name: Build frontend
        run: pnpm -C admin-ui build
```

Day 1 CI 不运行 scripts.check_llm，也不需要启动数据库，因为今天的 API 测试没有连接它们。Day 2 接数据库测试时再增加对应 service 和迁移。

版本参考：[checkout release](https://github.com/actions/checkout/releases/tag/v7.0.1)、[setup-uv release](https://github.com/astral-sh/setup-uv/releases/tag/v10.3.0)、[setup-node release](https://github.com/actions/setup-node/releases/tag/v7.1.0)、[uv release](https://github.com/astral-sh/uv/releases/tag/0.13.4)

**十四、常见错误，从出现的那一步处理**

| 现象 | 先检查什么 | 正确处理 |
|---|---|---|
| uv 找不到 | 新终端 PATH、安装是否完成 | 重新打开终端验证 Get-Command uv |
| Docker 只有 Client | Desktop Linux engine 是否启动 | 等待启动并确认 Server，再运行 Compose |
| ModuleNotFoundError: app | 是否在项目根目录、是否用了 -m | 回到 ResearchMate，运行模块命令 |
| health 返回404 | 路由是否注册、prefix 是否重复 | /api 只注册一次，完整路径 /api/health |
| 配置始终 false | .env 是否在根目录、字段名和缓存 | 校对三项配置，重启后端 |
| 页面 fetch 失败 | 后端是否启动、Vite代理目标/端口 | 单独访问 API，再检查 /api 代理 |
| uvicorn 窗口不返回提示符 | 服务是否正在运行 | 保留该终端，换新终端执行其它命令 |
| 5173/8000 端口占用 | 是否已经开了另一个服务 | 找到实际进程，只停止自己开的重复服务 |
| CI 找不到锁文件 | 本地生成后是否已提交 | 依赖声明和 uv.lock/pnpm-lock.yaml 一起提交 |
| 模型401/404/429 | Key、Base URL、服务配额 | 按预检 HTTP 状态核对服务配置 |
| 没有工具调用 | 工具schema、Prompt、模型/接口能力 | 记录未收到，不冒充成功，进一步核对能力 |
| Git push被拒绝 | 远程是否空仓库、认证和历史 | 查看真实错误与历史，不用强推掩盖 |

最后核对：[Day 1 收工验收](./Day01-逐步实操.md)和 [每日记录模板](./每日记录模板.md)。教学示例通过静态检查不等于你的应用已部署成功；后端、页面、容器、真实模型和 GitHub CI 需要按步骤分别实际运行。

