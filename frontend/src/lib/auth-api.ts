const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  location?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  token?: {
    access_token: string;
    token_type: string;
    expires_in: number;
    user_id: number;
    email: string;
    first_name: string;
  };
  user_id?: number;
}

export interface TokenData {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: number;
  email: string;
  first_name: string;
}

// Authentication API functions
export const authAPI = {
  // Register a new user
  async register(data: RegisterRequest): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  // Login user
  async login(data: LoginRequest): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  // Change password (requires authentication)
  async changePassword(currentPassword: string, newPassword: string, token: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Password change failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Password change error:', error);
      throw error;
    }
  },
};

// Token management utilities
export const tokenUtils = {
  // Save token to localStorage
  saveToken(token: TokenData): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', JSON.stringify(token));
    }
  },

  // Get token from localStorage
  getToken(): TokenData | null {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      return token ? JSON.parse(token) : null;
    }
    return null;
  },

  // Remove token from localStorage
  removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  },

  // Check if token is expired
  isTokenExpired(token: TokenData): boolean {
    // For now, we'll use a simple check based on expires_in
    // In a real app, you'd decode the JWT and check the exp claim
    return false; // Placeholder
  },

  // Get authorization header for API requests
  getAuthHeader(): { Authorization: string } | {} {
    const token = this.getToken();
    if (token && !this.isTokenExpired(token)) {
      return { Authorization: `Bearer ${token.access_token}` };
    }
    return {};
  },
}; 