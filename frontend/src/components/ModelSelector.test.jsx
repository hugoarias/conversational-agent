import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ModelSelector from '../components/ModelSelector.jsx';

// Mock the useModels hook so ModelSelector can be tested in isolation
vi.mock('../hooks/useModels.js', () => ({
  useModels: vi.fn(),
}));

import { useModels } from '../hooks/useModels.js';

const ollamaModels = [
  { id: 'llama3', name: 'llama3', provider: 'ollama' },
  { id: 'mistral', name: 'mistral', provider: 'ollama' },
];
const bedrockModels = [
  { id: 'claude', name: 'Claude 3 Haiku', provider: 'bedrock' },
];

describe('ModelSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state', () => {
    useModels.mockReturnValue({ ollamaModels: [], bedrockModels: [], loading: true, error: null });
    render(<ModelSelector selectedModel={{ provider: 'ollama', model: 'llama3' }} onSelect={() => {}} disabled={false} />);
    expect(screen.getByText(/loading models/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    useModels.mockReturnValue({ ollamaModels: [], bedrockModels: [], loading: false, error: 'Failed' });
    render(<ModelSelector selectedModel={{ provider: 'ollama', model: 'llama3' }} onSelect={() => {}} disabled={false} />);
    expect(screen.getByText(/could not load models/i)).toBeInTheDocument();
  });

  it('renders ollama models in dropdown', () => {
    useModels.mockReturnValue({ ollamaModels, bedrockModels: [], loading: false, error: null });
    render(<ModelSelector selectedModel={{ provider: 'ollama', model: 'llama3' }} onSelect={() => {}} disabled={false} />);
    expect(screen.getByRole('option', { name: 'llama3' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'mistral' })).toBeInTheDocument();
  });

  it('renders bedrock models in dropdown', () => {
    useModels.mockReturnValue({ ollamaModels: [], bedrockModels, loading: false, error: null });
    render(<ModelSelector selectedModel={{ provider: 'bedrock', model: 'claude' }} onSelect={() => {}} disabled={false} />);
    expect(screen.getByRole('option', { name: 'Claude 3 Haiku' })).toBeInTheDocument();
  });

  it('shows "no models available" when both lists are empty', () => {
    useModels.mockReturnValue({ ollamaModels: [], bedrockModels: [], loading: false, error: null });
    render(<ModelSelector selectedModel={{ provider: 'ollama', model: '' }} onSelect={() => {}} disabled={false} />);
    expect(screen.getByText(/no models available/i)).toBeInTheDocument();
  });

  it('select is disabled when disabled prop is true', () => {
    useModels.mockReturnValue({ ollamaModels, bedrockModels: [], loading: false, error: null });
    render(<ModelSelector selectedModel={{ provider: 'ollama', model: 'llama3' }} onSelect={() => {}} disabled={true} />);
    expect(screen.getByRole('combobox')).toBeDisabled();
  });

  it('select is enabled when disabled prop is false', () => {
    useModels.mockReturnValue({ ollamaModels, bedrockModels: [], loading: false, error: null });
    render(<ModelSelector selectedModel={{ provider: 'ollama', model: 'llama3' }} onSelect={() => {}} disabled={false} />);
    expect(screen.getByRole('combobox')).not.toBeDisabled();
  });

  it('calls onSelect with provider and model when value changes', () => {
    useModels.mockReturnValue({ ollamaModels, bedrockModels: [], loading: false, error: null });
    const onSelect = vi.fn();
    render(<ModelSelector selectedModel={{ provider: 'ollama', model: 'llama3' }} onSelect={onSelect} disabled={false} />);

    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'ollama:mistral' } });
    expect(onSelect).toHaveBeenCalledWith({ provider: 'ollama', model: 'mistral' });
  });
});
