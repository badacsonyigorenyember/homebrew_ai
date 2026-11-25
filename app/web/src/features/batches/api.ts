import { useQuery } from '@tanstack/react-query';

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

export function useBatches() {
  return useQuery({
    queryKey: ['batches'],
    queryFn: fetchBatches,
  });
}

export function useBrewableBatches() {
  return useQuery({
    queryKey: ['recipes', 'brewable'],
    queryFn: fetchBrewableRecipes,
  });
}
