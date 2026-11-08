import { HealthBadge } from '@/features/health/HealthBadge.tsx';
import { Outlet } from 'react-router';

export function AppLayout() {
  return (
    <div className="min-h-svh flex flex-col">
      <header className="flex h-14 items-center gap-2">
        <span>Brewing App</span>
        <span className="ml-auto">
          <HealthBadge />
        </span>
      </header>
      <aside className="w-56 shrink-0"></aside>
      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
