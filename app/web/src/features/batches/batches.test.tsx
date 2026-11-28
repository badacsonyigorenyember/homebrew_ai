import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw/http';
import { describe, expect, it } from 'vitest';
import { renderApp } from '@/test/renderApp';
import { server } from '@/test/server';
import type { BatchSummary } from '@/features/batches/api';

const firstBatch: BatchSummary = {
  id: 7,
  number: 1,
  name: 'First brew',
  styleCode: '10A',
  styleName: 'Weissbier',
  brewDate: '2026-11-28',
  status: 'brew_day',
};

describe('batches', () => {
  it('lists the batches', async () => {
    server.use(http.get('/api/batches', () => HttpResponse.json([firstBatch])));
    renderApp('/batches');

    expect(
      await screen.findByRole('row', {
        name: '1 First brew 10A Weissbier 2026-11-28 Brew day',
      }),
    ).toBeInTheDocument();
  });
});
