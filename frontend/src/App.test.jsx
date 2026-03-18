import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'

describe('App RAG query flow', () => {
  test('submits query and renders response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        answer: 'Example answer',
        retrieval_mode_used: 'faiss',
        model: 'gpt-4o-mini',
        latency_ms: 18.2,
        sources: [{ title: 'Movie A', description: 'A', score: 0.9 }],
      }),
    })

    render(<App />)

    fireEvent.change(screen.getByPlaceholderText(/Ask about Netflix content/i), {
      target: { value: 'Best thriller titles?' },
    })
    fireEvent.click(screen.getByRole('button', { name: /run query/i }))

    await waitFor(() => {
      expect(screen.getByText('Example answer')).toBeInTheDocument()
    })
    expect(screen.getByText(/Retrieval:\s*faiss/i)).toBeInTheDocument()
    expect(screen.getByText(/Model: gpt-4o-mini/i)).toBeInTheDocument()
    expect(screen.getByText(/Latency: 18.2 ms/i)).toBeInTheDocument()
  })

  test('renders error state when API fails', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Rate limit exceeded' }),
    })

    render(<App />)

    fireEvent.change(screen.getByPlaceholderText(/Ask about Netflix content/i), {
      target: { value: 'Any thriller?' },
    })
    fireEvent.click(screen.getByRole('button', { name: /run query/i }))

    await waitFor(() => {
      expect(screen.getByText(/Rate limit exceeded/i)).toBeInTheDocument()
    })
  })
})
