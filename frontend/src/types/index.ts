export interface BackgroundTask {
  id: string;
  task_type: string;
  reference_id: string;
  status: "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED";
  result?: Record<string, unknown>;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskCreatedResponse {
  task_id: string;
}
