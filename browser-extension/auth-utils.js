// Authentication utilities for Job Application Agent extension
class AuthUtils {
  constructor() {
    this.apiBaseUrl = 'http://localhost:8000';
  }

  async getStoredAuth() {
    try {
      const result = await chrome.storage.local.get(['userToken', 'currentUser', 'tokenExpiry']);
      return {
        token: result.userToken,
        user: result.currentUser,
        expiry: result.tokenExpiry
      };
    } catch (error) {
      console.error('Error getting stored auth:', error);
      return { token: null, user: null, expiry: null };
    }
  }

  async storeAuth(token, user, expiresIn = 604800) {
    try {
      // Set expiry to 7 days (604800 seconds) for longer sessions
      const expiry = Date.now() + (expiresIn * 1000);
      await chrome.storage.local.set({
        userToken: token,
        currentUser: user,
        tokenExpiry: expiry,
        lastActivity: Date.now()
      });
      return true;
    } catch (error) {
      console.error('Error storing auth:', error);
      return false;
    }
  }

  async clearAuth() {
    try {
      await chrome.storage.local.remove(['userToken', 'currentUser', 'tokenExpiry', 'lastActivity']);
      return true;
    } catch (error) {
      console.error('Error clearing auth:', error);
      return false;
    }
  }

  async isTokenValid(token) {
    if (!token) return false;

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/auth/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      return response.ok;
    } catch (error) {
      console.error('Error verifying token:', error);
      return false;
    }
  }

  async verifyAndRefreshAuth() {
    const result = await chrome.storage.local.get(['userToken', 'currentUser', 'tokenExpiry', 'lastActivity']);
    const { userToken: token, currentUser: user, tokenExpiry: expiry, lastActivity } = result;

    // Check if token exists
    if (!token) {
      return { valid: false, user: null };
    }

    // Check if token has expired (7 days)
    if (expiry && Date.now() > expiry) {
      console.log('Token expired, clearing auth');
      await this.clearAuth();
      return { valid: false, user: null };
    }

    // Update last activity
    await chrome.storage.local.set({ lastActivity: Date.now() });

    // Only verify with server occasionally (every hour) to avoid constant API calls
    const shouldVerifyServer = !lastActivity || (Date.now() - lastActivity) > (60 * 60 * 1000);
    
    if (shouldVerifyServer) {
      console.log('Verifying token with server...');
      const isValid = await this.isTokenValid(token);
      if (!isValid) {
        console.log('Server validation failed, clearing auth');
        await this.clearAuth();
        return { valid: false, user: null };
      }
    }

    return { valid: true, user: user, token: token };
  }

  async getUserProfile(token) {
    try {
      const verifyResponse = await fetch(`${this.apiBaseUrl}/api/auth/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!verifyResponse.ok) {
        throw new Error('Token verification failed');
      }

      const verifyData = await verifyResponse.json();
      const userId = verifyData.user_id;

      // Get full user profile
      const profileResponse = await fetch(`${this.apiBaseUrl}/api/users/${userId}/profile`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!profileResponse.ok) {
        throw new Error('Failed to fetch user profile');
      }

      return await profileResponse.json();
    } catch (error) {
      console.error('Error getting user profile:', error);
      return null;
    }
  }

  async loginUser(email, password) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: email,
          password: password
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const authData = await response.json();
      
      // Store authentication data
      await this.storeAuth(authData.access_token, authData.user);
      
      return { success: true, user: authData.user, token: authData.access_token };
    } catch (error) {
      console.error('Error logging in:', error);
      return { success: false, error: error.message };
    }
  }

  openLoginPage() {
    const frontendUrl = this.apiBaseUrl.replace('8000', '3000');
    chrome.tabs.create({ url: `${frontendUrl}/login` });
  }

  openDashboard() {
    const frontendUrl = this.apiBaseUrl.replace('8000', '3000');
    chrome.tabs.create({ url: frontendUrl });
  }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AuthUtils;
} else if (typeof window !== 'undefined') {
  window.AuthUtils = AuthUtils;
}