import { StatusBadge, type ApiStatus } from './components/StatusBadge';
import { useHealth } from './features/health/useHealth';

const statusLookup: Record<'pending' | 'error' | 'success', ApiStatus> = {
  pending: 'unknown',
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
