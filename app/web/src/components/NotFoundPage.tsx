import { Link } from 'react-router';

export function NotFoundPage() {
  return (
    <div>
      <h1 className={'text-2xl font-semibold'}>Page not found</h1>
      <Link to={'/batches'}>Batches</Link>
    </div>
  );
}
