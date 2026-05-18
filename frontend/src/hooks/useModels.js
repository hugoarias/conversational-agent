import { useState, useEffect } from 'react';

/**
 * Fetches available LLM models from the backend's GET /api/models endpoint.
 * Returns models grouped by provider for easy rendering.
 */
export function useModels() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchModels() {
      try {
        const res = await fetch('/api/models');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) setModels(data.models ?? []);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchModels();
    return () => { cancelled = true; };
  }, []);

  const ollamaModels = models.filter(m => m.provider === 'ollama');
  const bedrockModels = models.filter(m => m.provider === 'bedrock');

  return { models, ollamaModels, bedrockModels, loading, error };
}
