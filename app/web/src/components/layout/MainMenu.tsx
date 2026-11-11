import { NavLink } from 'react-router';
import { cn } from '@/lib/utils';

const menuItems = [
  { to: '/batches', label: 'Batches' },
  { to: '/recipes', label: 'Recipes' },
  { to: '/inventory', label: 'Inventory' },
  { to: '/devices', label: 'Devices' },
  { to: '/settings', label: 'Settings' },
];

type MainMenuProps = { onNavigate?: () => void };

export function MainMenu({ onNavigate }: MainMenuProps) {
  return (
    <nav aria-label="Main">
      <ul>
        {menuItems.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  'block rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground',
                  isActive && 'bg-accent text-accent-foreground font-medium',
                )
              }
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
