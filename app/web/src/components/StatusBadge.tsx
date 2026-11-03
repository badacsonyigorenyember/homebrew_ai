type ApiStatus = 'ok' | 'down' | 'unknown';

type StatusBadgeProps = {
  status: ApiStatus;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const labels: Record<ApiStatus, string> = {
    ok: 'API ok',
    down: 'API down',
    unknown: 'API status unknown',
  };

  return <span>{labels[status]}</span>;
}
