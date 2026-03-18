import { useState } from 'react'

function QueryForm({ onSubmit, loading }) {
  const [question, setQuestion] = useState('')
  const [retrievalMode, setRetrievalMode] = useState('auto')

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!question.trim()) return
    onSubmit({ question: question.trim(), retrievalMode })
  }

  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Ask about Netflix content trends, genres, or recommendations..."
        rows={4}
      />
      <select
        value={retrievalMode}
        onChange={(event) => setRetrievalMode(event.target.value)}
        disabled={loading}
      >
        <option value="auto">Auto (FAISS with DB fallback)</option>
        <option value="faiss">FAISS only</option>
        <option value="db">Database only</option>
      </select>
      <button type="submit" disabled={loading}>
        {loading ? 'Analyzing...' : 'Run Query'}
      </button>
    </form>
  )
}

export default QueryForm
