import React from 'react';
import { useModels } from '../hooks/useModels.js';

/**
 * Dropdown that lists available LLM models grouped by provider.
 * Disabled while a conversation session is active to prevent mid-session changes.
 *
 * @param {{ provider: string, model: string }} selectedModel
 * @param {function} onSelect - Called with { provider, model } on change
 * @param {boolean}  disabled - Disable while conversation is running
 */
export default function ModelSelector({ selectedModel, onSelect, disabled }) {
  const { ollamaModels, bedrockModels, loading, error } = useModels();

  const handleChange = (e) => {
    const [provider, ...rest] = e.target.value.split(':');
    onSelect({ provider, model: rest.join(':') });
  };

  const value = `${selectedModel.provider}:${selectedModel.model}`;

  if (loading) {
    return <div className="model-selector model-selector--loading">Loading models…</div>;
  }

  if (error) {
    return <div className="model-selector model-selector--error">⚠ Could not load models</div>;
  }

  return (
    <div className="model-selector">
      <label className="model-selector__label" htmlFor="model-select">Model</label>
      <select
        id="model-select"
        className="model-selector__select"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        title={disabled ? 'Pause the conversation to change the model' : 'Select a model'}
      >
        {ollamaModels.length > 0 && (
          <optgroup label="🖥 Local (Ollama)">
            {ollamaModels.map(m => (
              <option key={m.id} value={`ollama:${m.id}`}>{m.name}</option>
            ))}
          </optgroup>
        )}
        {bedrockModels.length > 0 && (
          <optgroup label="☁ AWS Bedrock">
            {bedrockModels.map(m => (
              <option key={m.id} value={`bedrock:${m.id}`}>{m.name}</option>
            ))}
          </optgroup>
        )}
        {ollamaModels.length === 0 && bedrockModels.length === 0 && (
          <option disabled value="">No models available</option>
        )}
      </select>
    </div>
  );
}
