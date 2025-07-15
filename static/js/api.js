// API client for Flask backend communication
class ApiClient {
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for session management
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }
      
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication
  async login(username, password) {
    return this.request('/api/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async logout() {
    return this.request('/api/logout', {
      method: 'POST',
    });
  }

  async getSession() {
    return this.request('/api/session');
  }

  // Remises
  async getRemises() {
    return this.request('/api/remises');
  }

  async getNextRemiseNumber() {
    return this.request('/api/next-remise-number');
  }

  async addRemise(remiseData) {
    return this.request('/api/remises', {
      method: 'POST',
      body: JSON.stringify(remiseData),
    });
  }

  async deleteRemise(remiseId) {
    return this.request(`/api/remises/${remiseId}`, {
      method: 'DELETE',
    });
  }

  // Users (admin only)
  async getUsers() {
    return this.request('/api/users');
  }

  async addUser(userData) {
    return this.request('/api/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async updateUser(userId, userData) {
    return this.request(`/api/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(userId) {
    return this.request(`/api/users/${userId}`, {
      method: 'DELETE',
    });
  }
}

// Create global API client instance
window.apiClient = new ApiClient();

