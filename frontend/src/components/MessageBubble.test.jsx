import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MessageBubble from '../components/MessageBubble.jsx';

describe('MessageBubble', () => {
  it('renders "You" label for user role', () => {
    render(<MessageBubble role="user" text="Hello there" />);
    expect(screen.getByText('You')).toBeInTheDocument();
    expect(screen.getByText('Hello there')).toBeInTheDocument();
  });

  it('renders "Agent" label for assistant role', () => {
    render(<MessageBubble role="assistant" text="Hi, how can I help?" />);
    expect(screen.getByText('Agent')).toBeInTheDocument();
    expect(screen.getByText('Hi, how can I help?')).toBeInTheDocument();
  });

  it('renders warning icon for error role', () => {
    render(<MessageBubble role="error" text="Something went wrong" />);
    expect(screen.getByText('⚠️')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('applies the correct CSS class based on role', () => {
    const { container } = render(<MessageBubble role="user" text="test" />);
    expect(container.firstChild).toHaveClass('message--user');
  });

  it('applies assistant CSS class for assistant role', () => {
    const { container } = render(<MessageBubble role="assistant" text="test" />);
    expect(container.firstChild).toHaveClass('message--assistant');
  });
});
