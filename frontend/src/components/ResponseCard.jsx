import ReactMarkdown from 'react-markdown'

function ResponseCard({ response = '', loading, error, result }) {
  // Prefer explicit `response` string, fall back to `result.answer` if provided
  const text = response || (result && (result.answer || ''))

  return (
    <section
      style={{
        width: '100%',
        background: '#ffffff',
        borderRadius: '16px',
        boxShadow: '0 8px 24px rgba(15, 23, 42, 0.08)',
        border: '1px solid #e2e8f0',
        padding: '1rem 1.25rem',
        overflowWrap: 'anywhere',
      }}
      aria-label="RAG response"
    >
      <h2 style={{ margin: '0 0 0.75rem', color: '#0f172a' }}>RAG Response</h2>

      {loading && <div style={{ color: '#64748b' }}>Loading response...</div>}
      {error && <div style={{ color: '#b91c1c' }}>{error}</div>}

      {!loading && !error && (
        <>
          {result && (
            <div style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {result.retrieval_mode_used && (
                <span style={{ background: '#eef2ff', padding: '0.2rem 0.5rem', borderRadius: '8px', fontSize: '0.85rem' }}>
                  Retrieval: {result.retrieval_mode_used}
                </span>
              )}
              {result.model && (
                <span style={{ background: '#ecfeff', padding: '0.2rem 0.5rem', borderRadius: '8px', fontSize: '0.85rem' }}>
                  Model: {result.model}
                </span>
              )}
              {result.latency_ms != null && (
                <span style={{ background: '#f0fdf4', padding: '0.2rem 0.5rem', borderRadius: '8px', fontSize: '0.85rem' }}>
                  Latency: {result.latency_ms} ms
                </span>
              )}
            </div>
          )}

          <div style={{ color: '#1e293b', lineHeight: 1.65, fontSize: '0.98rem' }}>
            <ReactMarkdown
              components={{
                ul: ({ node, ...props }) => (
                  <ul style={{ paddingLeft: '1.25rem', margin: '0.6rem 0' }} {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol style={{ paddingLeft: '1.25rem', margin: '0.6rem 0' }} {...props} />
                ),
                li: ({ node, ...props }) => <li style={{ marginBottom: '0.35rem' }} {...props} />,
                strong: ({ node, ...props }) => <strong style={{ color: '#0b172a' }} {...props} />,
                p: ({ node, ...props }) => <p style={{ margin: '0.5rem 0' }} {...props} />,
              }}
            >
              {text || 'No response yet. Run a query to see RAG output.'}
            </ReactMarkdown>
          </div>

          {result?.sources?.length > 0 && (
            <div style={{ marginTop: '0.75rem' }}>
              <h3 style={{ margin: '0.5rem 0' }}>Retrieved Sources</h3>
              <ul style={{ paddingLeft: '1rem' }}>
                {result.sources.map((s, i) => (
                  <li key={`${s.title}-${i}`} style={{ marginBottom: '0.45rem' }}>
                    <strong>{s.title}</strong>
                    <span style={{ marginLeft: '0.5rem', color: '#475569' }}>Score: {s.score}</span>
                    {s.description && <div style={{ marginTop: '0.25rem' }}>{s.description}</div>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  )
}

export default ResponseCard
