/**
 * API functions for connecting to the FastAPI backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface Question {
  id: string
  question: string
}

export interface StartJobResponse {
  job_id: string
  task: string
  questions: Question[]
}

export interface Provider {
  id: number
  job_id: string
  name: string
  phone: string | null
  estimated_price: number | null
  negotiated_price?: number | null
  call_status?: string | null
  raw_result?: Record<string, unknown>
}

export interface Job {
  id: string
  original_query: string
  task: string
  zip_code: string
  date_needed: string
  price_limit: number | string
  clarifications: Record<string, string>
  questions: Question[]
  status: string
}

export interface CompleteJobResponse {
  job: Job
  providers: Provider[]
}

/**
 * Start a new job - calls Grok LLM to infer task and generate questions
 */
export async function startJob(
  query: string,
  houseAddress: string,
  zipCode: string,
  priceLimit: string,
  dateNeeded: string
): Promise<StartJobResponse> {
  // Parse price limit: remove "$", convert "No Limit" to "no_limit"
  let parsedPriceLimit: number | string
  if (priceLimit === "No Limit" || priceLimit === "no_limit") {
    parsedPriceLimit = "no_limit"
  } else {
    parsedPriceLimit = parseInt(priceLimit.replace("$", ""), 10)
  }

  // Format date as YYYY-MM-DD
  const formattedDate = formatDate(dateNeeded)

  const response = await fetch(`${API_URL}/api/start-job`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      house_address: houseAddress,
      zip_code: zipCode,
      price_limit: parsedPriceLimit,
      date_needed: formattedDate,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || "Failed to start job")
  }

  return response.json()
}

/**
 * Complete a job with answers - searches for providers
 */
export async function completeJob(
  jobId: string,
  answers: Record<string, string>
): Promise<CompleteJobResponse> {
  const response = await fetch(`${API_URL}/api/complete-job`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_id: jobId,
      answers,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || "Failed to complete job")
  }

  return response.json()
}

/**
 * Get provider status for a job (includes call status and negotiated prices)
 */
export async function getProviderStatus(jobId: string): Promise<Provider[]> {
  const response = await fetch(`${API_URL}/api/providers/${jobId}/status`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || "Failed to get provider status")
  }

  return response.json()
}

/**
 * Start calls for all providers in a job
 */
export async function startCalls(jobId: string): Promise<{ status: string; message: string; provider_count: number }> {
  const response = await fetch(`${API_URL}/api/start-calls/${jobId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || "Failed to start calls")
  }

  return response.json()
}

/**
 * Format date string to YYYY-MM-DD
 * Handles formats like "December 15th, 2025" or "Dec 15, 2025"
 */
function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      // If parsing fails, return as-is (backend will handle)
      return dateStr
    }
    return date.toISOString().split("T")[0]
  } catch {
    return dateStr
  }
}

