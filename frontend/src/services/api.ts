/**
 * TB Personal OS - API Service
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ApiResponse, ApiError } from '../types';

// ==========================================
// API CLIENT
// ==========================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8090';
const API_KEY = import.meta.env.VITE_API_KEY || '';

class ApiService {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth headers
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        if (API_KEY) {
          config.headers['X-API-Key'] = API_KEY;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<{ detail?: string }>) => {
        const apiError: ApiError = {
          message: error.response?.data?.detail || error.message || 'Unknown error',
          code: error.code,
          details: error.response?.data as Record<string, unknown> | undefined,
        };
        return Promise.reject(apiError);
      }
    );
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  // ==========================================
  // GENERIC METHODS
  // ==========================================

  async get<T = any>(path: string, params?: Record<string, any>): Promise<T> {
    const response = await this.client.get(path, { params });
    return response.data;
  }

  async post<T = any>(path: string, data?: Record<string, any>): Promise<T> {
    const response = await this.client.post(path, data);
    return response.data;
  }

  async put<T = any>(path: string, data?: Record<string, any>): Promise<T> {
    const response = await this.client.put(path, data);
    return response.data;
  }

  async patch<T = any>(path: string, data?: Record<string, any>): Promise<T> {
    const response = await this.client.patch(path, data);
    return response.data;
  }

  async delete<T = any>(path: string): Promise<T> {
    const response = await this.client.delete(path);
    return response.data;
  }

  // ==========================================
  // TASKS API
  // ==========================================

  async getTasks(params?: { status?: string; limit?: number }) {
    const response = await this.client.get('/tasks', { params });
    return response.data;
  }

  async getTasksToday() {
    const response = await this.client.get('/tasks/today');
    return response.data;
  }

  async getTasksOverdue() {
    const response = await this.client.get('/tasks/overdue');
    return response.data;
  }

  async createTask(data: {
    title: string;
    description?: string;
    priority?: string;
    due_date?: string;
  }) {
    const response = await this.client.post('/tasks', data);
    return response.data;
  }

  async updateTask(taskId: string, data: Record<string, any>) {
    const response = await this.client.patch(`/tasks/${taskId}`, data);
    return response.data;
  }

  async completeTask(taskId: string) {
    const response = await this.client.patch(`/tasks/${taskId}`, {
      status: 'completed',
    });
    return response.data;
  }

  async deleteTask(taskId: string) {
    await this.client.delete(`/tasks/${taskId}`);
  }

  // ==========================================
  // INBOX API
  // ==========================================

  async getInbox(params?: { status?: string; limit?: number }) {
    const response = await this.client.get('/inbox', { params });
    return response.data;
  }

  async createInboxItem(data: { content: string; source?: string }) {
    const response = await this.client.post('/inbox', data);
    return response.data;
  }

  async processInboxItem(itemId: string) {
    const response = await this.client.post(`/inbox/${itemId}/process`);
    return response.data;
  }

  async archiveProcessedInbox() {
    const response = await this.client.post('/inbox/archive-processed');
    return response.data;
  }

  // ==========================================
  // PROJECTS API
  // ==========================================

  async getProjects(params?: { status?: string }) {
    const response = await this.client.get('/projects/', { params });
    return response.data;
  }

  async createProject(data: { name: string; description?: string }) {
    const response = await this.client.post('/projects/', data);
    return response.data;
  }

  async getProjectTasks(projectId: string) {
    const response = await this.client.get(`/projects/${projectId}/tasks`);
    return response.data;
  }

  // ==========================================
  // CHECKINS API
  // ==========================================

  async getCheckinsSummary() {
    const response = await this.client.get('/checkins/summary');
    return response.data;
  }

  async getCheckinsToday() {
    const response = await this.client.get('/checkins/today');
    return response.data;
  }

  async checkinEnergy(level: number, notes?: string) {
    const response = await this.client.post('/checkins/energy', { level, notes });
    return response.data;
  }

  async checkinMood(mood: string, score?: number, notes?: string) {
    const response = await this.client.post('/checkins/mood', { mood, score, notes });
    return response.data;
  }

  async checkinSleep(hours: number, quality?: number, notes?: string) {
    const response = await this.client.post('/checkins/sleep', { hours, quality, notes });
    return response.data;
  }

  // ==========================================
  // CALENDAR API
  // ==========================================

  async getCalendarEventsToday() {
    const response = await this.client.get('/calendar/events/today');
    return response.data;
  }

  async getCalendarEventsWeek() {
    const response = await this.client.get('/calendar/events/week');
    return response.data;
  }

  async getGoogleAuthStatus() {
    const response = await this.client.get('/auth/google/status');
    return response.data;
  }

  async getGoogleLoginUrl() {
    const response = await this.client.get('/auth/google/login');
    return response.data;
  }

  // ==========================================
  // ASSISTANT API
  // ==========================================

  async askAssistant(question: string) {
    const response = await this.client.post('/assistant/ask', { question });
    return response.data;
  }

  async processMessage(message: string) {
    const response = await this.client.post('/assistant/process', { message });
    return response.data;
  }

  async getMorningSummary() {
    const response = await this.client.get('/assistant/summary/morning');
    return response.data;
  }

  async getNightSummary() {
    const response = await this.client.get('/assistant/summary/night');
    return response.data;
  }

  async getAssistantContext() {
    const response = await this.client.get('/assistant/context');
    return response.data;
  }

  // ==========================================
  // SCHEDULER API
  // ==========================================

  async getSchedulerJobs() {
    const response = await this.client.get('/scheduler/jobs');
    return response.data;
  }

  async runRoutine(routineType: 'morning' | 'night' | 'weekly') {
    const response = await this.client.post('/scheduler/run', {
      routine_type: routineType,
    });
    return response.data;
  }

  // ==========================================
  // HEALTH CHECK
  // ==========================================

  async healthCheck() {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  }
}

export const api = new ApiService();
export default api;
