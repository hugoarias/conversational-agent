import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useModels } from '../hooks/useModels.js';

describe('useModels', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('starts in loading state', () => {
    fetch.mockReturnValue(new Promise(() => {})); // never resolves
    const { result } = renderHook(() => useModels());
    expect(result.current.loading).toBe(true);
    expect(result.current.models).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('returns models split by provider on success', async () => {
    const mockData = {
      models: [
        { id: 'llama3', name: 'llama3', provider: 'ollama' },
        { id: 'claude', name: 'Claude', provider: 'bedrock' },
      ],
    };
    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const { result } = renderHook(() => useModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.ollamaModels).toHaveLength(1);
    expect(result.current.bedrockModels).toHaveLength(1);
    expect(result.current.ollamaModels[0].id).toBe('llama3');
    expect(result.current.bedrockModels[0].id).toBe('claude');
    expect(result.current.error).toBeNull();
  });

  it('sets error state on non-OK HTTP response', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 503,
    });

    const { result } = renderHook(() => useModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('HTTP 503');
    expect(result.current.models).toEqual([]);
  });

  it('sets error state on network failure', async () => {
    fetch.mockRejectedValue(new Error('network error'));

    const { result } = renderHook(() => useModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('network error');
    expect(result.current.models).toEqual([]);
  });

  it('returns empty arrays when models list is empty', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ models: [] }),
    });

    const { result } = renderHook(() => useModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.ollamaModels).toEqual([]);
    expect(result.current.bedrockModels).toEqual([]);
  });

  it('handles missing models key in response', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });

    const { result } = renderHook(() => useModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.models).toEqual([]);
  });
});
