import { Badge } from '@/components/ui/badge';

export type ApiStatus = 'ok' | 'down' | 'unknown';

type StatusBadgeProps = {
  status: ApiStatus;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const labels: Record<ApiStatus, string> = {
    ok: 'API ok',
    down: 'API down',
    unknown: 'API status unknown',
  };

  const variants: Record<ApiStatus, 'default' | 'destructive' | 'secondary'> = {
    down: 'destructive',
    ok: 'default',
    unknown: 'secondary',
  };

  return <Badge variant={variants[status]}>{labels[status]}</Badge>;
}
