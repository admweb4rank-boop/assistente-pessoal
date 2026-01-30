/**
 * TB Personal OS - TypeScript Types
 */

// ==========================================
// USER TYPES
// ==========================================

export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  preferences?: UserPreferences;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  notifications?: boolean;
  language?: string;
  timezone?: string;
}

// ==========================================
// AUTH TYPES
// ==========================================

export interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export interface Session {
  access_token: string;
  refresh_token?: string;
  expires_at?: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials extends LoginCredentials {
  full_name?: string;
}

// ==========================================
// TASK TYPES
// ==========================================

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: Priority;
  due_date?: string;
  due_time?: string;
  project_id?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'archived';
export type Priority = 'low' | 'medium' | 'high' | 'urgent';

export interface CreateTaskInput {
  title: string;
  description?: string;
  priority?: Priority;
  due_date?: string;
  due_time?: string;
  project_id?: string;
  tags?: string[];
}

export interface UpdateTaskInput extends Partial<CreateTaskInput> {
  status?: TaskStatus;
}

// ==========================================
// PROJECT TYPES
// ==========================================

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  priority: Priority;
  color: string;
  icon: string;
  start_date?: string;
  target_date?: string;
  completed_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus = 'active' | 'completed' | 'archived' | 'paused';

// ==========================================
// INBOX TYPES
// ==========================================

export interface InboxItem {
  id: string;
  user_id: string;
  content: string;
  source: InboxSource;
  source_metadata?: Record<string, any>;
  status: InboxStatus;
  processed_at?: string;
  result_task_id?: string;
  created_at: string;
  updated_at: string;
}

export type InboxSource = 'telegram' | 'web' | 'voice' | 'email' | 'api';
export type InboxStatus = 'pending' | 'processed' | 'archived';

// ==========================================
// CHECKIN TYPES
// ==========================================

export interface Checkin {
  id: string;
  user_id: string;
  checkin_type: CheckinType;
  value: number;
  notes?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export type CheckinType = 'energy' | 'mood' | 'sleep' | 'workout' | 'custom';

export interface CheckinStats {
  type: CheckinType;
  avg_value: number;
  min_value: number;
  max_value: number;
  total_count: number;
  last_checkin?: string;
}

// ==========================================
// CALENDAR TYPES
// ==========================================

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  location?: string;
  is_all_day: boolean;
  status: 'confirmed' | 'tentative' | 'cancelled';
  metadata?: Record<string, any>;
}

// ==========================================
// API TYPES
// ==========================================

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  status: number;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// ==========================================
// ASSISTANT TYPES
// ==========================================

export interface AssistantMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface AssistantContext {
  tasks_today: number;
  tasks_overdue: number;
  inbox_pending: number;
  next_event?: CalendarEvent;
  energy_level?: number;
  mood?: string;
}

export interface ProcessMessageResponse {
  intent: string;
  response: string;
  actions?: AssistantAction[];
  suggestions?: string[];
}

export interface AssistantAction {
  type: string;
  data: Record<string, any>;
}
