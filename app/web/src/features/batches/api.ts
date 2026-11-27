import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export type BatchStatus =
  'plan' | 'prep' | 'brew_day' | 'ferment' | 'condition' | 'package' | 'done';

export type BatchSummary = {
  id: number;
  number: number;
  name: string;
  styleCode: string;
  styleName: string | null;
  brewDate: string;
  status: BatchStatus;
};

export type BrewableRecipe = {
  id: number;
  styleCode: string;
  styleName: string | null;
  og: number | null;
  fg: number | null;
  abv: number | null;
  ibu: number | null;
  batchL: number;
  createdAt: string;
};

export type CreateBatchRequest = {
  recipeId: number;
  name: string;
  brewDate: string;
};

export type CreatedBatch = {
  id: number;
  number: number;
  name: string;
};

export type ProblemDetails = {
  title?: string;
  detail?: string;
  status?: number;
  errors?: Record<string, string[]>;
};

export class ApiProblemError extends Error {
  problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(problem.detail ?? problem.title ?? 'There is some problem.');

    this.problem = problem;
  }
}

async function fetchBatches(): Promise<BatchSummary[]> {
  const response = await fetch('/api/batches');

  if (!response.ok) {
    throw new Error(response.statusText);
  }

  return response.json();
}

async function fetchBrewableRecipes(): Promise<BrewableRecipe[]> {
  const response = await fetch('/api/recipes/brewable');

  if (!response.ok) {
    throw new Error(response.statusText);
  }

  return response.json();
}

async function createBatch(request: CreateBatchRequest): Promise<CreatedBatch> {
  const response = await fetch('/api/batches', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (response.headers.get('Content-Type') === 'application/problem+json') {
    throw new ApiProblemError(await response.json());
  }

  if (!response.ok) {
    throw new Error(response.statusText);
  }

  return response.json();
}

export function useBatches() {
  return useQuery({
    queryKey: ['batches'],
    queryFn: fetchBatches,
  });
}

export function useBrewableRecipes() {
  return useQuery({
    queryKey: ['recipes', 'brewable'],
    queryFn: fetchBrewableRecipes,
  });
}

export function useCreateBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createBatch,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['batches'] }),
  });
}
