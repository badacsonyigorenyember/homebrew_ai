import { Navigate, Route, Routes } from 'react-router';
import { BatchesPage } from '@/features/batches/BatchesPage';
import { DevicesPage } from '@/features/devices/DevicesPage';
import { InventoryPage } from '@/features/inventory/InventoryPage';
import { RecipesPage } from '@/features/recipes/RecipesPage';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { NotFoundPage } from '@/components/NotFoundPage';
import { AppLayout } from './components/layout/AppLayout';

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="batches" replace />}></Route>
        <Route path={'batches'} element={<BatchesPage />}></Route>
        <Route path={'devices'} element={<DevicesPage />}></Route>
        <Route path={'inventory'} element={<InventoryPage />}></Route>
        <Route path={'recipes'} element={<RecipesPage />}></Route>
        <Route path={'settings'} element={<SettingsPage />}></Route>
        <Route path={'*'} element={<NotFoundPage />}></Route>
      </Route>
    </Routes>
  );
}

export default App;
