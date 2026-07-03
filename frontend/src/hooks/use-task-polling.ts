"use client";

import { useQuery } from "@tanstack/react-query";
import type { BackgroundTask } from "@/types";
import { api } from "@/lib/api-client";

interface UseTaskPollingOptions {
  taskId: string | null;
  onComplete?: (task: BackgroundTask) => void;
  onError?: (task: BackgroundTask) => void;
}

export function useTaskPolling({ taskId, onComplete, onError }: UseTaskPollingOptions) {
  const query = useQuery<BackgroundTask>({
    queryKey: ["task", taskId],
    queryFn: () => api.get(`tasks/${taskId}`).json(),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "COMPLETED" || status === "FAILED") return false;
      // Exponential backoff: 2s → 4s → 8s, capped at 10s
      return Math.min(2000 * Math.pow(2, query.state.dataUpdateCount), 10_000);
    },
  });

  const task = query.data;

  if (task?.status === "COMPLETED" && onComplete) {
    onComplete(task);
  }
  if (task?.status === "FAILED" && onError) {
    onError(task);
  }

  return {
    task,
    isPolling: !!taskId && task?.status !== "COMPLETED" && task?.status !== "FAILED",
    isCompleted: task?.status === "COMPLETED",
    isFailed: task?.status === "FAILED",
    ...query,
  };
}
