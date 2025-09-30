import { create } from 'zustand';

interface ResultState {
  results: any[];
  isLoading: boolean;
  selectedResult: any | null;
  setResults: (results: any[]) => void;
  setLoading: (loading: boolean) => void;
  setSelectedResult: (result: any | null) => void;
  addResult: (result: any) => void;
  removeResult: (resultId: string) => void;
}

export const useResultStore = create<ResultState>((set) => ({
  results: [],
  isLoading: false,
  selectedResult: null,
  setResults: (results) => set({ results }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSelectedResult: (result) => set({ selectedResult: result }),
  addResult: (result) => set((state) => ({ 
    results: [...state.results, result] 
  })),
  removeResult: (resultId) => set((state) => ({ 
    results: state.results.filter(r => r.id !== resultId) 
  })),
}));
