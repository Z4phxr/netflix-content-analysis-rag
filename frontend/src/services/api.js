const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function queryRag(question, retrievalMode = 'auto') {
  const response = await fetch(`${API_BASE_URL}/api/v1/rag/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ question, retrieval_mode: retrievalMode })
  })

  if (!response.ok) {
    let detail = 'Failed to fetch RAG response'
    try {
      const payload = await response.json()
      detail = payload.detail || detail
    } catch {
      // ignore JSON parse failures and keep default message
    }
    throw new Error(detail)
  }

  return response.json()
}
