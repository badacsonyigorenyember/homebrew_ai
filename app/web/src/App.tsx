import { Navigate, Route, Routes } from 'react-router';
import { BatchesPage } from '@/features/batches/BatchesPage';
import { RecipesPage } from '@/features/recipes/RecipesPage';
import { InventoryPage } from '@/features/inventory/InventoryPage';
import { DevicesPage } from '@/features/devices/DevicesPage';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { NotFoundPage } from '@/components/NotFoundPage';
import { AppLayout } from './components/layout/AppLayout';
import { BatchPage } from '@/features/batches/BatchPage.tsx';

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="batches" replace />}></Route>
        <Route path={'batches'} element={<BatchesPage />}></Route>
        <Route path={'batches/:id'} element={<BatchPage />}></Route>
        <Route path={'recipes'} element={<RecipesPage />}></Route>
        <Route path={'inventory'} element={<InventoryPage />}></Route>
        <Route path={'devices'} element={<DevicesPage />}></Route>
        <Route path={'settings'} element={<SettingsPage />}></Route>
        <Route path={'*'} element={<NotFoundPage />}></Route>
      </Route>
    </Routes>
  );
}

export default App;
