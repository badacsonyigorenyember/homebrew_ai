import { useQuery } from '@tanstack/react-query';

type HealthResponse = {
  status: string;
};

async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch('api/health');

  if (!response.ok) {
    throw new Error(
      `An error happened during health check: ${response.statusText}`,
    );
  }

  return response.json();
}

export function useHealth() {
  return useQuery({ queryKey: ['data'], queryFn: fetchHealth });
}
