import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ChatWindow from '../components/ChatWindow.jsx';

describe('ChatWindow', () => {
  it('shows empty state placeholder when no messages', () => {
    render(<ChatWindow messages={[]} />);
    expect(screen.getByText("Start speaking — I'm listening...")).toBeInTheDocument();
  });

  it('does not show empty placeholder when messages exist', () => {
    const messages = [{ id: '1', role: 'user', text: 'Hello' }];
    render(<ChatWindow messages={messages} />);
    expect(screen.queryByText("Start speaking — I'm listening...")).not.toBeInTheDocument();
  });

  it('renders all messages', () => {
    const messages = [
      { id: '1', role: 'user', text: 'First message' },
      { id: '2', role: 'assistant', text: 'Second message' },
    ];
    render(<ChatWindow messages={messages} />);
    expect(screen.getByText('First message')).toBeInTheDocument();
    expect(screen.getByText('Second message')).toBeInTheDocument();
  });

  it('renders inside a main element', () => {
    const { container } = render(<ChatWindow messages={[]} />);
    expect(container.querySelector('main')).toBeInTheDocument();
  });
});
