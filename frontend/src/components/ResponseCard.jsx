function ResponseCard({ loading, error, result }) {
  if (loading) return <div className="response-card">Loading response...</div>
  if (error) return <div className="response-card error">{error}</div>
  if (!result) return <div className="response-card">Submit a query to see results.</div>

  return (
    <div className="response-card">
      <h2>Response</h2>
      <p>{result.answer}</p>

      {result.sources?.length > 0 && (
        <>
          <h3>Retrieved Sources</h3>
          <ul>
            {result.sources.map((source, index) => (
              <li key={`${source.title}-${index}`}>
                <strong>{source.title}</strong>
                <span>Score: {source.score}</span>
                <p>{source.description}</p>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export default ResponseCard
