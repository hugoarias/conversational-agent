import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StatusBar from '../components/StatusBar.jsx';

describe('StatusBar', () => {
  it('shows connected label when wsStatus is open', () => {
    render(<StatusBar wsStatus="open" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
  });

  it('shows connecting label when wsStatus is connecting', () => {
    render(<StatusBar wsStatus="connecting" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByText('🟡 Connecting...')).toBeInTheDocument();
  });

  it('shows reconnecting label when wsStatus is reconnecting', () => {
    render(<StatusBar wsStatus="reconnecting" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByText('🟡 Reconnecting...')).toBeInTheDocument();
  });

  it('shows disconnected label when wsStatus is closed', () => {
    render(<StatusBar wsStatus="closed" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByText('🔴 Disconnected')).toBeInTheDocument();
  });

  it('shows error label when wsStatus is error', () => {
    render(<StatusBar wsStatus="error" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByText('🔴 Error')).toBeInTheDocument();
  });

  it('shows retry button when disconnected', () => {
    render(<StatusBar wsStatus="closed" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('shows retry button when error', () => {
    render(<StatusBar wsStatus="error" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('does NOT show retry button when connected', () => {
    render(<StatusBar wsStatus="open" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('does NOT show retry button when connecting', () => {
    render(<StatusBar wsStatus="connecting" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('calls onReconnect when retry button is clicked', async () => {
    const onReconnect = vi.fn();
    render(<StatusBar wsStatus="closed" vadStatus="idle" onReconnect={onReconnect} />);
    await userEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(onReconnect).toHaveBeenCalledTimes(1);
  });

  it('shows VAD idle label', () => {
    render(<StatusBar wsStatus="open" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByText('🎤 Idle')).toBeInTheDocument();
  });

  it('shows VAD recording label', () => {
    render(<StatusBar wsStatus="open" vadStatus="recording" onReconnect={() => {}} />);
    expect(screen.getByText('🔴 Recording')).toBeInTheDocument();
  });

  it('shows VAD listening label', () => {
    render(<StatusBar wsStatus="open" vadStatus="listening" onReconnect={() => {}} />);
    expect(screen.getByText('👂 Listening')).toBeInTheDocument();
  });

  it('shows unknown wsStatus as raw string', () => {
    render(<StatusBar wsStatus="custom-status" vadStatus="idle" onReconnect={() => {}} />);
    expect(screen.getByText('custom-status')).toBeInTheDocument();
  });
});
