/**
 * TB Personal OS - Supabase Auth Service
 */

import { createClient, SupabaseClient, User, Session } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

class AuthService {
  private supabase: SupabaseClient;
  private currentUser: User | null = null;
  private currentSession: Session | null = null;
  private authListeners: Set<(user: User | null) => void> = new Set();

  constructor() {
    this.supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    
    // Listen for auth changes
    this.supabase.auth.onAuthStateChange((event, session) => {
      this.currentSession = session;
      this.currentUser = session?.user ?? null;
      this.notifyListeners();
    });

    // Get initial session
    this.initSession();
  }

  private async initSession() {
    const { data: { session } } = await this.supabase.auth.getSession();
    this.currentSession = session;
    this.currentUser = session?.user ?? null;
    this.notifyListeners();
  }

  private notifyListeners() {
    this.authListeners.forEach(listener => listener(this.currentUser));
  }

  // ==========================================
  // AUTH METHODS
  // ==========================================

  async signUp(email: string, password: string, fullName?: string) {
    const { data, error } = await this.supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    });

    if (error) throw error;
    return data;
  }

  async signIn(email: string, password: string) {
    const { data, error } = await this.supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;
    return data;
  }

  async signInWithMagicLink(email: string) {
    const { data, error } = await this.supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/`,
      },
    });

    if (error) throw error;
    return data;
  }

  async signInWithGoogle() {
    const { data, error } = await this.supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (error) throw error;
    return data;
  }

  async signOut() {
    const { error } = await this.supabase.auth.signOut();
    if (error) throw error;
    this.currentUser = null;
    this.currentSession = null;
  }

  async resetPassword(email: string) {
    const { data, error } = await this.supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    });

    if (error) throw error;
    return data;
  }

  async updatePassword(newPassword: string) {
    const { data, error } = await this.supabase.auth.updateUser({
      password: newPassword,
    });

    if (error) throw error;
    return data;
  }

  // ==========================================
  // SESSION METHODS
  // ==========================================

  getUser(): User | null {
    return this.currentUser;
  }

  getSession(): Session | null {
    return this.currentSession;
  }

  getAccessToken(): string | null {
    return this.currentSession?.access_token ?? null;
  }

  isAuthenticated(): boolean {
    return !!this.currentSession;
  }

  // ==========================================
  // LISTENER METHODS
  // ==========================================

  onAuthChange(callback: (user: User | null) => void): () => void {
    this.authListeners.add(callback);
    // Return unsubscribe function
    return () => {
      this.authListeners.delete(callback);
    };
  }

  // ==========================================
  // SUPABASE CLIENT
  // ==========================================

  getSupabaseClient(): SupabaseClient {
    return this.supabase;
  }
}

export const authService = new AuthService();
export default authService;
