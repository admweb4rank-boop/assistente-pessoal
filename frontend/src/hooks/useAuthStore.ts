/**
 * TB Personal OS - Auth Store (Zustand)
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Session } from '@supabase/supabase-js';
import { authService } from '../services/auth';
import { api } from '../services/api';

interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  
  // Actions
  initialize: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName?: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      session: null,
      isLoading: true,
      isAuthenticated: false,
      error: null,

      initialize: async () => {
        set({ isLoading: true });
        
        // Subscribe to auth changes
        authService.onAuthChange((user) => {
          const session = authService.getSession();
          set({
            user,
            session,
            isAuthenticated: !!user,
            isLoading: false,
          });
          
          // Update API service with token
          api.setAccessToken(session?.access_token ?? null);
        });

        // Get initial state
        const user = authService.getUser();
        const session = authService.getSession();
        
        set({
          user,
          session,
          isAuthenticated: !!user,
          isLoading: false,
        });

        // Set initial token
        api.setAccessToken(session?.access_token ?? null);
      },

      signIn: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const { user, session } = await authService.signIn(email, password);
          
          set({
            user,
            session,
            isAuthenticated: !!user,
            isLoading: false,
          });
          
          api.setAccessToken(session?.access_token ?? null);
        } catch (error: any) {
          set({
            error: error.message || 'Failed to sign in',
            isLoading: false,
          });
          throw error;
        }
      },

      signUp: async (email: string, password: string, fullName?: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const { user, session } = await authService.signUp(email, password, fullName);
          
          set({
            user,
            session,
            isAuthenticated: !!user,
            isLoading: false,
          });
          
          api.setAccessToken(session?.access_token ?? null);
        } catch (error: any) {
          set({
            error: error.message || 'Failed to sign up',
            isLoading: false,
          });
          throw error;
        }
      },

      signInWithGoogle: async () => {
        set({ isLoading: true, error: null });
        
        try {
          await authService.signInWithGoogle();
          // Auth state will be updated via onAuthStateChange
        } catch (error: any) {
          set({
            error: error.message || 'Failed to sign in with Google',
            isLoading: false,
          });
          throw error;
        }
      },

      signOut: async () => {
        set({ isLoading: true, error: null });
        
        try {
          await authService.signOut();
          
          set({
            user: null,
            session: null,
            isAuthenticated: false,
            isLoading: false,
          });
          
          api.setAccessToken(null);
        } catch (error: any) {
          set({
            error: error.message || 'Failed to sign out',
            isLoading: false,
          });
          throw error;
        }
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'tb-auth-storage',
      partialize: (state) => ({ 
        // Don't persist sensitive data
      }),
    }
  )
);

export default useAuthStore;
