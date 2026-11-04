import { StatusBadge, type ApiStatus } from './components/StatusBadge';
import { useHealth } from './features/health/useHealth';

const statusLookup: Record<'pending' | 'error' | 'success', ApiStatus> = {
  pending: 'unknown',
  error: 'down',
  success: 'ok',
};

function App() {
  const health = useHealth();
  // A query that has never had data goes back to 'pending' on every refetch, so while
  // the API is down, `status` alone would flip to 'unknown' each time it asks again.
  // A recorded error means that 'pending' is "down, checking again".
  const status =
    health.status === 'pending' && health.errorUpdatedAt > 0
      ? 'down'
      : statusLookup[health.status];

  return (
    <div>
      <h1>Brewing App</h1>
      <StatusBadge status={status} />
    </div>
  );
}

export default App;
