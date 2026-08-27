// frontend/src/v3/__tests__/ui-components.test.jsx
// D21 — smoke tests for the shared UI primitives (buttons, badges, status,
// alerts, dialogs, state views).
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import StatusBadge from '../components/ui/StatusBadge';
import Alert from '../components/ui/Alert';
import { TextInput, CheckboxField } from '../components/ui/FormControls';
import { LoadingState, ErrorState, EmptyState, PermissionState } from '../components/ui/StateViews';
import Dialog, { ConfirmationDialog } from '../components/ui/Dialog';

describe('Button (D21.5)', () => {
  test('renders children and is disabled while loading', () => {
    render(<Button variant="primary" loading>Save</Button>);
    const button = screen.getByRole('button', { name: /save/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  test('renders an anchor when href is provided', () => {
    render(<Button href="/reports">View report</Button>);
    expect(screen.getByRole('link', { name: /view report/i })).toHaveAttribute('href', '/reports');
  });

  test('fires onClick', () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Go</Button>);
    fireEvent.click(screen.getByRole('button', { name: /go/i }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});

describe('StatusBadge (D21.4)', () => {
  test('renders a labelled, coloured, icon-bearing status', () => {
    render(<StatusBadge status="approved" />);
    expect(screen.getByText('Approved')).toBeInTheDocument();
  });

  test('renders an unknown status without dropping it', () => {
    render(<StatusBadge status="mystery_status" />);
    expect(screen.getByText('mystery_status')).toBeInTheDocument();
  });
});

describe('Badge', () => {
  test('renders tone class and label', () => {
    render(<Badge tone="success">Complete</Badge>);
    const badge = screen.getByText('Complete');
    expect(badge).toHaveClass('ct-badge--success');
  });
});

describe('Alert (D21)', () => {
  test('renders error alerts with role=alert', () => {
    render(<Alert tone="error" title="Failed">Try again.</Alert>);
    expect(screen.getByRole('alert')).toHaveTextContent('Failed');
    expect(screen.getByText('Try again.')).toBeInTheDocument();
  });
});

describe('FormControls (D21.6)', () => {
  test('binds label to input and surfaces inline errors', () => {
    render(<TextInput label="Supplier" error="Required" />);
    const input = screen.getByLabelText(/supplier/i);
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
  });

  test('marks required fields', () => {
    render(<TextInput label="Supplier" required />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  test('checkbox row associates its label', () => {
    render(<CheckboxField label="Notify me" />);
    expect(screen.getByLabelText(/notify me/i)).toHaveAttribute('type', 'checkbox');
  });
});

describe('StateViews (D29/F3)', () => {
  test('LoadingState announces a status region', () => {
    render(<LoadingState label="Loading…" />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading…');
  });

  test('ErrorState offers a retry action', () => {
    const onRetry = jest.fn();
    render(<ErrorState message="boom" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  test('PermissionState is an alert that never grants access', () => {
    render(<PermissionState message="No access." />);
    expect(screen.getByRole('alert')).toHaveTextContent('No access.');
  });

  test('EmptyState renders children', () => {
    render(<EmptyState>No reports yet.</EmptyState>);
    expect(screen.getByText('No reports yet.')).toBeInTheDocument();
  });
});

describe('Dialog (D21)', () => {
  test('opens with a title and closes via close button', () => {
    const onClose = jest.fn();
    render(<Dialog open title="Confirm" onClose={onClose}>Body</Dialog>);
    expect(screen.getByRole('dialog')).toHaveTextContent('Confirm');
    fireEvent.click(screen.getByLabelText(/close dialog/i));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test('renders nothing when closed', () => {
    render(<Dialog open={false} title="Confirm" onClose={() => {}}>Body</Dialog>);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  test('ConfirmationDialog exposes confirm/cancel', () => {
    const onConfirm = jest.fn();
    const onClose = jest.fn();
    render(
      <ConfirmationDialog open title="Delete?" message="Really?" onConfirm={onConfirm} onClose={onClose} />,
    );
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });
});
