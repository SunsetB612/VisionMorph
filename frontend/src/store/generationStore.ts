import { create } from 'zustand';

interface GenerationState {
  isGenerating: boolean;
  generationProgress: number;
  generatedImages: any[];
  setGenerating: (generating: boolean) => void;
  setProgress: (progress: number) => void;
  addGeneratedImage: (image: any) => void;
  clearGeneratedImages: () => void;
}

export const useGenerationStore = create<GenerationState>((set) => ({
  isGenerating: false,
  generationProgress: 0,
  generatedImages: [],
  setGenerating: (generating) => set({ isGenerating: generating }),
  setProgress: (progress) => set({ generationProgress: progress }),
  addGeneratedImage: (image) => set((state) => ({ 
    generatedImages: [...state.generatedImages, image] 
  })),
  clearGeneratedImages: () => set({ generatedImages: [] }),
}));
