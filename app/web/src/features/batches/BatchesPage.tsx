import { useBatches } from '@/features/batches/api.ts';
import { BatchList } from '@/features/batches/BatchList.tsx';

export function BatchesPage() {
  const batches = useBatches();

  return (
    <div className={'flex flex-col gap-4'}>
      <div className={'flex items-center justify-between gap-2'}>
        <h1 className={''}>Batches</h1>
      </div>
      {batches.isPending && <p>Loading batches…</p>}
      {batches.isError && (
        <p>The page could not be loaded: {batches.error.message}</p>
      )}
      {batches.isSuccess &&
        (batches.data.length === 0 ? (
          <p>No batches yet</p>
        ) : (
          <BatchList batches={batches.data} />
        ))}
    </div>
  );
}
