import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw/http';
import { describe, expect, it } from 'vitest';
import { renderApp } from '@/test/renderApp';
import { server } from '@/test/server';
import type { BatchSummary, BrewableRecipe } from '@/features/batches/api';
import { type UserEvent, userEvent } from '@testing-library/user-event';

const firstBatch: BatchSummary = {
  id: 7,
  number: 1,
  name: 'First brew',
  styleCode: '10A',
  styleName: 'Weissbier',
  brewDate: '2026-11-28',
  status: 'brew_day',
};

const weissbier: BrewableRecipe = {
  id: 1489,
  styleCode: '10A',
  styleName: 'Weissbier',
  og: 1.0481,
  fg: 1.0099,
  abv: 4.9,
  ibu: 11.8,
  batchL: 10,
  createdAt: '2026-11-04T09:18:21Z',
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

  it('shows "No batches yet" and the New batch button when there are none', async () => {
    renderApp('/batches');

    expect(await screen.findByText('No batches yet')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'New Batch' }),
    ).toBeInTheDocument();
  });

  it('creates a batch and opens its page', async () => {
    let batches: BatchSummary[] = [];
    let sent: unknown;

    server.use(
      http.get('/api/recipes/brewable', () => HttpResponse.json([weissbier])),
      http.get('/api/batches', () => HttpResponse.json(batches)),
      http.post('/api/batches', async ({ request }) => {
        sent = await request.json();
        batches = [{ ...firstBatch, name: 'Weissbier' }];
        return HttpResponse.json(
          { id: 7, number: 1, name: 'Weissbier' },
          { status: 201 },
        );
      }),
    );
    renderApp('/batches');

    await fillOutCreateBatchForm(userEvent.setup());

    expect(
      await screen.findByRole('heading', { name: 'Weissbier' }),
    ).toBeInTheDocument();
    expect(sent).toEqual({
      recipeId: 1489,
      name: 'Weissbier',
      brewDate: '2026-11-28',
    });
  });

  it("shows the API's message under the field it is about", async () => {
    server.use(
      http.get('/api/recipes/brewable', () => HttpResponse.json([weissbier])),
      http.post('/api/batches', () =>
        HttpResponse.json(
          {
            title: 'One or more validation errors occurred.',
            status: 400,
            errors: { Name: ['The Name field is required.'] },
          },
          {
            status: 400,
            headers: { 'Content-Type': 'application/problem+json' },
          },
        ),
      ),
    );
    renderApp('/batches');

    await fillOutCreateBatchForm(userEvent.setup());

    expect(await screen.findByText('The Name field is required.'));
    expect(screen.getByRole('textbox', { name: 'Name' })).toBeInvalid();
  });
});

async function fillOutCreateBatchForm(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'New Batch' }));
  await screen.findByRole('option', { name: /^Weissbier/ });
  await user.selectOptions(
    screen.getByRole('combobox', { name: 'Recipe' }),
    '1489',
  );
  await user.type(screen.getByLabelText('Brew date'), '2026-11-28');
  await user.click(screen.getByRole('button', { name: 'Create batch' }));
}
