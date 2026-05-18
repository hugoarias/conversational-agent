import { describe, it, expect } from 'vitest';
import { encodeWAV } from '../services/audioUtils.js';

describe('encodeWAV', () => {
  it('returns an ArrayBuffer', () => {
    const samples = new Float32Array([0, 0.5, -0.5]);
    const result = encodeWAV(samples, 16000);
    expect(result).toBeInstanceOf(ArrayBuffer);
  });

  it('produces correct total length (44-byte header + 2 bytes per sample)', () => {
    const samples = new Float32Array(100);
    const result = encodeWAV(samples, 16000);
    expect(result.byteLength).toBe(44 + 100 * 2);
  });

  it('writes RIFF header magic bytes', () => {
    const samples = new Float32Array(10);
    const buffer = encodeWAV(samples, 44100);
    const view = new DataView(buffer);
    const riff = String.fromCharCode(
      view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3)
    );
    const wave = String.fromCharCode(
      view.getUint8(8), view.getUint8(9), view.getUint8(10), view.getUint8(11)
    );
    expect(riff).toBe('RIFF');
    expect(wave).toBe('WAVE');
  });

  it('writes correct sample rate in header', () => {
    const samples = new Float32Array(10);
    const buffer = encodeWAV(samples, 22050);
    const view = new DataView(buffer);
    expect(view.getUint32(24, true)).toBe(22050);
  });

  it('clamps values above 1.0 to max int16', () => {
    const samples = new Float32Array([2.0]);
    const buffer = encodeWAV(samples, 16000);
    const view = new DataView(buffer);
    const sample = view.getInt16(44, true);
    expect(sample).toBe(32767);
  });

  it('clamps values below -1.0 to min int16', () => {
    const samples = new Float32Array([-2.0]);
    const buffer = encodeWAV(samples, 16000);
    const view = new DataView(buffer);
    const sample = view.getInt16(44, true);
    expect(sample).toBe(-32768);
  });

  it('encodes silence (0.0) as zero bytes', () => {
    const samples = new Float32Array([0.0]);
    const buffer = encodeWAV(samples, 16000);
    const view = new DataView(buffer);
    expect(view.getInt16(44, true)).toBe(0);
  });
});
