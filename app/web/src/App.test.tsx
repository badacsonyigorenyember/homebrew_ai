import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';
import { http, HttpResponse } from 'msw/http';
import { server } from './test/server';
import { MemoryRouter } from 'react-router';

function renderApp() {
  const queryClient = new QueryClient();

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('App', () => {
  it('shows "API status unknown" before the API answers', () => {
    renderApp();

    expect(screen.getByText('API status unknown')).toBeInTheDocument();
  });

  it('shows "API ok" when the API answers', async () => {
    renderApp();

    expect(await screen.findByText('API ok')).toBeInTheDocument();
  });

  it('shows "API down" when the API is stopped', async () => {
    server.use(
      http.get('/api/health', () => new HttpResponse(null, { status: 502 })),
    );
    renderApp();

    expect(
      await screen.findByText('API down', {}, { timeout: 2000 }),
    ).toBeInTheDocument();
  });

  it('shows "API down" when the API answers 500', async () => {
    server.use(
      http.get('/api/health', () =>
        HttpResponse.json(
          {
            title: 'An error occured while processing your request.',
            status: 500,
          },
          { status: 500 },
        ),
      ),
    );
    renderApp();

    expect(
      await screen.findByText('API down', {}, { timeout: 2000 }),
    ).toBeInTheDocument();
  });
});
