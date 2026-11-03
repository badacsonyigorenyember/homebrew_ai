import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from './StatusBadge.tsx';

describe('StatusBadge', () => {
  it('shows "API ok" when the status is ok', () => {
    render(<StatusBadge status="ok" />);

    expect(screen.getByText('API ok')).toBeInTheDocument();
  });
});

describe('StatusBadge', () => {
  it('shows "API down" when the status is down', () => {
    render(<StatusBadge status="down" />);

    expect(screen.getByText('API down')).toBeInTheDocument();
  });
});

describe('StatusBadge', () => {
  it('shows "API unknown" when the status is unknown', () => {
    render(<StatusBadge status="unknown" />);

    expect(screen.getByText('API status unknown')).toBeInTheDocument();
  });
});
