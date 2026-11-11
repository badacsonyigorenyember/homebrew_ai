import { HealthBadge } from '@/features/health/HealthBadge';
import { Outlet } from 'react-router';
import { MainMenu } from '@/components/layout/MainMenu';
import { useState } from 'react';
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { MenuIcon } from 'lucide-react';

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-svh flex flex-col">
      <header className="flex h-14 items-center gap-2">
        <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
          <SheetTrigger
            render={
              <Button
                variant="ghost"
                size="icon"
                aria-label="Open menu"
                className="md:hidden"
              />
            }
          >
            <MenuIcon />
          </SheetTrigger>
          <SheetContent side={'left'} className={'p-2'}>
            <SheetTitle>Brewing App</SheetTitle>
            <MainMenu onNavigate={() => setMenuOpen(false)} />
          </SheetContent>
        </Sheet>
        <span>Brewing App</span>
        <span className="ml-auto">
          <HealthBadge />
        </span>
      </header>
      <div className="flex flex-1">
        <aside className="w-56 shrink-0 border-r p-4 hidden md:block">
          <MainMenu />
        </aside>
        <main className="flex-1 min-w-0 px-4 border-b p-4 text-2xl font-semibold">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
