import { StatusBadge } from './components/StatusBadge';
import { useHealth } from './features/health/useHealth.ts';
import type { ApiStatus } from './components/StatusBadge';

const statusLookup: Record<'pending' | 'error' | 'success', ApiStatus> = {
  pending: 'unknown', // Adjust 'unknown' or 'down' based on your exact ticket instructions
  error: 'down',
  success: 'ok',
};

function App() {
  const health = useHealth();

  return (
    <div>
      <h1>Brewing App</h1>
      <StatusBadge status={statusLookup[health.status]} />
    </div>
  );
}

export default App;
