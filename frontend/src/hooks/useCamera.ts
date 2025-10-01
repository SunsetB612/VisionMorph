import { useState, useRef, useCallback, useEffect } from 'react';

interface CameraState {
  isActive: boolean;
  isCapturing: boolean;
  error: string | null;
  stream: MediaStream | null;
  isVideoReady: boolean;
  facingMode: 'user' | 'environment';
}

export const useCamera = () => {
  const [state, setState] = useState<CameraState>({
    isActive: false,
    isCapturing: false,
    error: null,
    stream: null,
    isVideoReady: false,
    facingMode: 'environment'
  });

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // 视频事件监听
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onLoadedMetadata = () => {
      setState(prev => ({ ...prev, isVideoReady: true }));
    };
    
    const onCanPlay = () => {
      setState(prev => ({ ...prev, isVideoReady: true }));
    };
    
    const onError = () => {
      setState(prev => ({ ...prev, error: '视频播放错误' }));
    };

    video.addEventListener('loadedmetadata', onLoadedMetadata);
    video.addEventListener('canplay', onCanPlay);
    video.addEventListener('error', onError);

    return () => {
      video.removeEventListener('loadedmetadata', onLoadedMetadata);
      video.removeEventListener('canplay', onCanPlay);
      video.removeEventListener('error', onError);
    };
  }, [state.isActive, state.stream]);

  // 设置视频流
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !state.stream || !state.isActive) return;
    
    // 强制设置新的视频流
    video.srcObject = state.stream;
    
    // 确保视频播放
    video.play().catch(() => {
      // 自动播放失败，等待用户交互
    });
  }, [state.stream, state.isActive]);

  const startCamera = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, error: null }));

      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: state.facingMode
          }
        });
      } catch (error) {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true
        });
      }
      
      setState(prev => ({ 
        ...prev, 
        stream, 
        isActive: true
      }));
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : '摄像头启动失败'
      }));
    }
  }, [state.facingMode]);

  const stopCamera = useCallback(() => {
    if (state.stream) {
      state.stream.getTracks().forEach(track => track.stop());
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setState(prev => ({
      ...prev,
      isActive: false,
      stream: null,
      isVideoReady: false
    }));
  }, [state.stream]);

  const capturePhoto = useCallback((): Promise<File> => {
    return new Promise((resolve, reject) => {
      if (!videoRef.current || !canvasRef.current) {
        reject(new Error('摄像头未初始化'));
        return;
      }

      const video = videoRef.current;
      
      if (!video.videoWidth || !video.videoHeight) {
        reject(new Error('视频未准备好，无法拍照'));
        return;
      }

      setState(prev => ({ ...prev, isCapturing: true }));

      try {
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        if (!context) {
          throw new Error('无法获取画布上下文');
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
          if (!blob) {
            reject(new Error('无法生成图片'));
            return;
          }

          const file = new File([blob], `camera_${Date.now()}.jpg`, {
            type: 'image/jpeg'
          });

          setState(prev => ({ ...prev, isCapturing: false }));
          resolve(file);
        }, 'image/jpeg', 0.9);
      } catch (error) {
        setState(prev => ({ ...prev, isCapturing: false }));
        reject(error);
      }
    });
  }, []);

  const flipCamera = useCallback(async () => {
    if (!state.isActive) return;

    try {
      // 1. 停止当前流
      if (state.stream) {
        state.stream.getTracks().forEach(track => track.stop());
      }

      // 2. 清理视频元素
      if (videoRef.current) {
        videoRef.current.srcObject = null;
        videoRef.current.load(); 
      }

      // 3. 更新状态
      const newFacingMode = state.facingMode === 'environment' ? 'user' : 'environment';
      setState(prev => ({ 
        ...prev, 
        facingMode: newFacingMode, 
        isVideoReady: false,
        stream: null,
        error: null
      }));

      // 4. 短暂延迟后重新启动摄像头
      setTimeout(async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              facingMode: newFacingMode
            }
          });
          
          setState(prev => ({ 
            ...prev, 
            stream, 
            isActive: true
          }));
        } catch (error) {
          // 如果指定摄像头失败，尝试通用摄像头
          try {
            const stream = await navigator.mediaDevices.getUserMedia({
              video: true
            });
            
            setState(prev => ({ 
              ...prev, 
              stream, 
              isActive: true
            }));
          } catch (fallbackError) {
            setState(prev => ({ 
              ...prev, 
              error: `切换摄像头失败: ${fallbackError instanceof Error ? fallbackError.message : '未知错误'}` 
            }));
          }
        }
      }, 100); // 100ms延迟确保清理完成

    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: `切换摄像头失败: ${error instanceof Error ? error.message : '未知错误'}` 
      }));
    }
  }, [state.isActive, state.stream, state.facingMode]);

  return {
    ...state,
    videoRef,
    canvasRef,
    startCamera,
    stopCamera,
    capturePhoto,
    flipCamera
  };
};