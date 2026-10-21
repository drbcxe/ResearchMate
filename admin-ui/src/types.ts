export interface HealthStatus {
  status: string
  version: string
}

export interface SettingsStatus {
  model_configured: boolean
  model_name: string
  base_url_host: string
}