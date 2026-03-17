import { useState } from 'react'

function QueryForm({ onSubmit, loading }) {
  const [question, setQuestion] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!question.trim()) return
    onSubmit(question.trim())
  }

  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Ask about Netflix content trends, genres, or recommendations..."
        rows={4}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Analyzing...' : 'Run Query'}
      </button>
    </form>
  )
}

export default QueryForm
