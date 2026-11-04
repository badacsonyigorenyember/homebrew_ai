import { useQuery } from '@tanstack/react-query';

type HealthResponse = {
  status: string;
};

async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health');

  if (!response.ok) {
    throw new Error(
      `An error happened during health check: ${response.status}`,
    );
  }

  return response.json();
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    // The API is on the home network and a stopped one is refused at once, so fail fast:
    // one retry after 1 s rides out a single dropped request. Asking every 5 s means a
    // stopped API shows as down about 1 s after the page loads, or within about 6 s
    // (next refetch + the retry) when the page is already open, and a restarted one
    // shows as ok again within 5 s.
    retry: 1,
    retryDelay: 1000,
    refetchInterval: 5000,
  });
}
