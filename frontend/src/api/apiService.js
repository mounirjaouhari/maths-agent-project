// frontend/src/api/apiService.js

// Base URL for the API Gateway (to be configured based on environment)
// In production, this would be an environment variable injected at build time
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/v1';

// Function to handle API requests
const callApi = async (endpoint, method = 'GET', data = null, authRequired = true) => {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (authRequired) {
    const token = localStorage.getItem('accessToken'); // Retrieve JWT token from local storage
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    } else {
      // If token is missing for an authenticated request,
      // redirect to login page or throw a specific error.
      // For now, we'll throw an error that can be caught by the calling component.
      throw new Error('Authentication token missing. Please log in again.');
    }
  }

  const config = {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (response.status === 401) {
      // Handle 401 Unauthorized globally: clear token and redirect to login
      localStorage.removeItem('accessToken');
      // This assumes a global redirect mechanism, e.g., in App.js or a context provider
      window.location.href = '/login'; // Redirect to login page
      throw new Error('Unauthorized: Session expired or invalid token.');
    }

    if (!response.ok) {
      let errorDetail = 'Something went wrong with the API request.';
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.message || errorDetail;
      } catch (parseError) {
        // If response is not JSON, use status text
        errorDetail = response.statusText || errorDetail;
      }
      throw new Error(`API Error ${response.status}: ${errorDetail}`);
    }

    // Handle 204 No Content responses
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('API call error:', error);
    throw error;
  }
};

// --- Specific functions for API Gateway endpoints ---

const apiService = {
  // Authentication and Users
  registerUser: async (userData) => {
    return callApi('/users/register', 'POST', userData, false); // No authentication required for registration
  },

  loginUser: async (username, password) => {
    // For our current implementation with JSON for login:
    const response = await callApi('/users/login', 'POST', { username, password }, false);
    if (response && response.access_token) {
      localStorage.setItem('accessToken', response.access_token);
    }
    return response;
  },

  // Projects
  getProjects: async (statusFilter = '') => {
    const endpoint = statusFilter ? `/projects?status=${statusFilter}` : '/projects';
    return callApi(endpoint);
  },

  getProject: async (projectId) => {
    return callApi(`/projects/${projectId}`);
  },

  createProject: async (projectData) => {
    return callApi('/projects', 'POST', projectData);
  },

  updateProject: async (projectId, updateData) => {
    return callApi(`/projects/${projectId}`, 'PUT', updateData);
  },

  deleteProject: async (projectId) => {
    return callApi(`/projects/${projectId}`, 'DELETE');
  },

  // Workflow and Signals
  sendWorkflowSignal: async (projectId, signalData) => {
    return callApi(`/projects/${projectId}/signal`, 'POST', signalData);
  },

  // QC Reports
  getQcReportForBlock: async (blockId) => {
    return callApi(`/content-blocks/${blockId}/qc-report`);
  },

  // Document Export
  downloadExportedDocument: async (exportId) => {
    // The endpoint returns a download URL, the browser handles the download
    return callApi(`/exports/${exportId}/download`);
  },

  // Update a content block (for manual editing)
  updateContentBlock: async (blockId, updateData) => {
    // This endpoint is not directly in the API Gateway OpenAPI,
    // but it would be an internal call to the Persistence Service or a dedicated endpoint
    // if the API Gateway proxies it. For the example, we simulate it here.
    // In reality, saving an edited block could be a workflow action
    // or a direct call to the persistence service via a secured API Gateway endpoint.
    // For now, we'll simulate a direct PUT call if the API Gateway supports it.
    // If the API Gateway does not support it, this logic should be reviewed.
    console.warn("updateContentBlock: This call simulates a direct update. Verify the actual API Gateway implementation.");
    return callApi(`/content-blocks/${blockId}`, 'PUT', updateData); // Assuming a direct PUT endpoint for blocks
  },
};

export default apiService;
