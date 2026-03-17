import QueryForm from './components/QueryForm'
import ResponseCard from './components/ResponseCard'
import { useRagQuery } from './hooks/useRagQuery'

function App() {
  const { loading, error, result, runQuery } = useRagQuery()

  return (
    <main className="app-shell">
      <section className="app-card">
        <h1>Netflix Content Analysis</h1>
        <p className="subtitle">Query the RAG service for contextual insights.</p>
        <QueryForm onSubmit={runQuery} loading={loading} />
        <ResponseCard loading={loading} error={error} result={result} />
      </section>
    </main>
  )
}

export default App
