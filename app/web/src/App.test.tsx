import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';
import { http, HttpResponse } from 'msw/http';
import { server } from './test/server';
import { MemoryRouter } from 'react-router';
import { userEvent } from '@testing-library/user-event';

function renderApp(path = '/') {
  const queryClient = new QueryClient();

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
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

describe('routes', () => {
  it('opens Batches at /', () => {
    renderApp();

    expect(
      screen.getByRole('heading', { name: 'Batches' }),
    ).toBeInTheDocument();
  });

  it('opens a page directly from its URL', () => {
    renderApp('/inventory');

    expect(
      screen.getByRole('heading', { name: 'Inventory' }),
    ).toBeInTheDocument();
  });

  it('shows the page of a clicked menu link and marks the link current', async () => {
    const user = userEvent.setup();
    renderApp('/batches');

    await user.click(screen.getByRole('link', { name: 'Recipes' }));

    expect(
      screen.getByRole('heading', { name: 'Recipes' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Recipes' })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });

  it('shows "Page not found" for an unknown path', () => {
    renderApp('/asd');

    expect(
      screen.queryByRole('heading', { name: 'Page not found' }),
    ).toBeInTheDocument();
  });
});
