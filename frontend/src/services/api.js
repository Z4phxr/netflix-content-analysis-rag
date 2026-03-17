const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function queryRag(question) {
  const response = await fetch(`${API_BASE_URL}/api/v1/rag/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ question })
  })

  if (!response.ok) {
    throw new Error('Failed to fetch RAG response')
  }

  return response.json()
}
