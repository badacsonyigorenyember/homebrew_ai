import { HealthBadge } from '@/features/health/HealthBadge';
import { Outlet } from 'react-router';
import { MainMenu } from '@/components/layout/MainMenu';

export function AppLayout() {
  return (
    <div className="min-h-svh flex flex-col">
      <header className="flex h-14 items-center gap-2">
        <span>Brewing App</span>
        <span className="ml-auto">
          <HealthBadge />
        </span>
      </header>
      <div className="flex flex-1">
        <aside className="w-56 shrink-0 border-r p-4">
          <MainMenu />
        </aside>
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
