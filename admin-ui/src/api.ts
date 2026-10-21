import type { HealthStatus, SettingsStatus } from './types'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

async function getJson<T>(
  path: string,
  parse: (value: unknown) => T,
  signal?: AbortSignal,
): Promise<T> {
  try {
    const timeout = AbortSignal.timeout(10_000)
    const response = await fetch(path, {
      credentials: 'include',
      cache: 'no-store',
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    })

    if (!response.ok) throw new Error('请求失败：HTTP ' + response.status)
    if (!response.headers.get('content-type')?.includes('application/json')) {
      throw new Error('接口未返回 JSON，请检查 /api 代理配置')
    }
    return parse(await response.json())
  } catch (error) {
    if (signal?.aborted) throw error
    if (error instanceof Error && error.name === 'TimeoutError') {
      throw new Error('请求超过 10 秒，请确认后端已启动后重试', { cause: error })
    }
    if (error instanceof TypeError) {
      throw new Error('无法连接服务，请检查网络和后端运行状态', { cause: error })
    }
    throw error
  }
}

export function getHealth(signal?: AbortSignal): Promise<HealthStatus> {
  return getJson('/api/health', (value) => {
    if (!isRecord(value) || typeof value.status !== 'string' || typeof value.version !== 'string') {
      throw new Error('健康检查接口返回格式不符合约定')
    }
    return { status: value.status, version: value.version }
  }, signal)
}

export function getSettingsStatus(signal?: AbortSignal): Promise<SettingsStatus> {
  return getJson('/api/settings/status', (value) => {
    if (
      !isRecord(value)
      || typeof value.model_configured !== 'boolean'
      || typeof value.model_name !== 'string'
      || typeof value.base_url_host !== 'string'
    ) {
      throw new Error('模型配置接口返回格式不符合约定')
    }
    return {
      model_configured: value.model_configured,
      model_name: value.model_name,
      base_url_host: value.base_url_host,
    }
  }, signal)
}
