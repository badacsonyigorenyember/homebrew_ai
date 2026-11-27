import type { BatchStatus, BatchSummary } from '@/features/batches/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Link } from 'react-router';

const statusLabels: Record<BatchStatus, string> = {
  plan: 'Plan',
  prep: 'Prep',
  brew_day: 'Brew day',
  ferment: 'Ferment',
  condition: 'Condition',
  package: 'Package',
  done: 'Done',
};

function styleText(batch: BatchSummary): string {
  return batch.styleName === null
    ? batch.styleCode
    : batch.styleCode + ' ' + batch.styleName;
}

type BatchListProps = { batches: BatchSummary[] };

export function BatchList({ batches }: BatchListProps) {
  return (
    <>
      <Table className="hidden md:table">
        <TableHeader>
          <TableRow>
            <TableHead>No.</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Style</TableHead>
            <TableHead>Brew date</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {batches.map((batch) => (
            <TableRow key={batch.id}>
              <TableCell>{batch.number}</TableCell>
              <TableCell>
                <Link
                  to={`/batches/${batch.id}`}
                  className={'font-medium hover:underline'}
                >
                  {batch.name}
                </Link>
              </TableCell>
              <TableCell>{styleText(batch)}</TableCell>
              <TableCell>{batch.brewDate}</TableCell>
              <TableCell>{statusLabels[batch.status]}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <ul className="md:hidden flex flex-col gap-2">
        {batches.map((batch) => (
          <li key={batch.id} className="border p-3 rounded-lg wrap-break-word">
            <p>
              #{batch.number}{' '}
              <Link
                to={`/batches/${batch.id}`}
                className={'font-medium hover:underline'}
              >
                {batch.name}
              </Link>
            </p>
            <p className={'text-sm text-muted-foreground'}>
              {styleText(batch)}
              {' · '}
              {batch.brewDate}
              {' · '}
              {statusLabels[batch.status]}
            </p>
          </li>
        ))}
      </ul>
    </>
  );
}
