import { useCallback } from 'react';

const VECTOR_LENGTH = 32;

export function useSyntheticBiometric() {
  const generate = useCallback(() => {
    const vector: number[] = [];
    for (let i = 0; i < VECTOR_LENGTH; i += 1) {
      const value = parseFloat((Math.random() * 2 - 1).toFixed(4));
      vector.push(value);
    }
    return vector;
  }, []);

  return { generate, vectorLength: VECTOR_LENGTH };
}
