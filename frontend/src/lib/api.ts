import type {
  ApprovalRequest,
  ApprovalResponse,
  LocationRequest,
  MemoryResponse,
  PendingApprovalResponse,
  RunHistoryResponse,
  RunResponse,
} from "@/lib/types"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }

  return (await response.json()) as T
}

export function runWorkflow(payload: LocationRequest): Promise<RunResponse> {
  return request<RunResponse>("/run", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function approveAlert(payload: ApprovalRequest): Promise<ApprovalResponse> {
  return request<ApprovalResponse>("/approve", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function rejectAlert(payload: ApprovalRequest): Promise<ApprovalResponse> {
  return request<ApprovalResponse>("/reject", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function getMemoryRules(): Promise<MemoryResponse> {
  return request<MemoryResponse>("/memory")
}

export function getRunHistory(): Promise<RunHistoryResponse> {
  return request<RunHistoryResponse>("/runs")
}

export function getPendingApproval(): Promise<PendingApprovalResponse> {
  return request<PendingApprovalResponse>("/pending")
}
