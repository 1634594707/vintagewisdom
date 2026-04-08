import { useState, useEffect, useRef } from 'react';
import { api, TaskStatusResponse } from '@/lib/api';
import { APIError } from '@/lib/api-error';

export function useTaskPolling(
  taskId: string | null,
  options: {
    interval?: number;
    onComplete?: (result: TaskStatusResponse) => void;
    onError?: (error: APIError) => void;
  } = {}
) {
  const { interval = 1000, onComplete, onError } = options;
  const [status, setStatus] = useState<TaskStatusResponse | null>(null);
  const [error, setError] = useState<APIError | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const poll = async () => {
      try {
        const result = await api.getTaskStatus(taskId);
        setStatus(result);

        if (result.status === 'completed') {
          onComplete?.(result);
          return true;
        }
        
        if (result.status === 'failed') {
          const err = new APIError(500, 'Task Failed', result.error_message || 'Unknown error', '');
          setError(err);
          onError?.(err);
          return true;
        }
      } catch (err) {
        const apiError = err instanceof APIError ? err : new APIError(0, '', String(err), '');
        setError(apiError);
        onError?.(apiError);
        return true;
      }
      return false;
    };

    poll();

    timerRef.current = setInterval(async () => {
      const shouldStop = await poll();
      if (shouldStop && timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }, interval);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [taskId, interval, onComplete, onError]);

  return { status, error };
}
