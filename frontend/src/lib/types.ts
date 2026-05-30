export type LocationRequest = {
  lat: number
  lon: number
  location_name?: string
}

export type LocationState = {
  latitude: number
  longitude: number
  name?: string
}

export type WeatherRecord = {
  time: string
  temperature: number
  humidity: number
  rainfall: number
  wind_speed: number
  pressure: number
}

export type ForecastPoint = {
  time: string
  rainfall: number
  rainfall_lower?: number
  rainfall_upper?: number
}

export type ForecastFeatures = {
  predicted_rainfall?: number
  temperature_trend?: number
  humidity?: number
  wind_speed?: number
  pressure?: number
}

export type ForecastResult = {
  horizon_hours?: number
  points?: ForecastPoint[]
  plot_path?: string
  features?: ForecastFeatures
}

export type DisasterPrediction = {
  most_likely?: string
} & Record<string, number | string | undefined>

export type RunState = {
  run_id?: string
  location?: LocationState
  weather_data?: WeatherRecord[]
  forecast?: ForecastResult
  disaster_prediction?: DisasterPrediction
  news_context?: string[]
  severity?: string
  severity_reason?: string
  routed_department?: string
  generated_alert?: string
  action_plan?: string[]
  approval_status?: string
  feedback?: string
  memory_rules?: string[]
}

export type RunResponse = {
  state: RunState
}

export type MemoryRule = {
  timestamp: string
  department: string
  rule: string
  run_id?: string
}

export type MemoryResponse = {
  rules: MemoryRule[]
}

export type RunLogEntry = {
  timestamp: string
  run_id?: string
  location_name?: string
  latitude?: number
  longitude?: number
  location?: string
  severity?: string
  routed_department?: string
  approval_status?: string
  most_likely?: string
}

export type RunHistoryResponse = {
  runs: RunLogEntry[]
}

export type PendingApproval = {
  run_id?: string
  routed_department?: string
  severity?: string
  generated_alert?: string
  action_plan?: string[]
}

export type PendingApprovalResponse = {
  pending: PendingApproval[]
}

export type ApprovalRequest = {
  run_id: string
  feedback?: string
}

export type ApprovalResponse = {
  status: "APPROVED" | "REJECTED"
  run_id: string
  feedback?: string
}
