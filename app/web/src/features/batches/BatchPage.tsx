import { useParams } from 'react-router';
import { useBatches } from '@/features/batches/api.ts';

export function BatchPage() {
  const { id } = useParams();
  const batches = useBatches();

  if (batches.isPending) {
    return <p>Loading...</p>;
  }

  if (batches.isError) {
    return <p>Something went wrong: {batches.error.message}</p>;
  }

  const batch = batches.data.find((b) => String(b.id) === id);

  return (
    <h1 className={'text-2xl font-semibold'}>
      {batch !== undefined ? batch.name : 'Batch not found.'}
    </h1>
  );
}
