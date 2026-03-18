import { useState } from 'react'
import { queryRag } from '../services/api'

export function useRagQuery() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const runQuery = async ({ question, retrievalMode }) => {
    setLoading(true)
    setError('')

    try {
      const data = await queryRag(question, retrievalMode)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Unexpected error while querying API')
    } finally {
      setLoading(false)
    }
  }

  return { loading, error, result, runQuery }
}
