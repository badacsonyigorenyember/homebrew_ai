import { Link } from 'react-router';

export function NotFoundPage() {
  return (
    <div>
      <h1>Page not found</h1>
      <Link to={'/batches'}>Batches</Link>
    </div>
  );
}
