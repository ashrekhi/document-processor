import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
console.log('API URL being used:', API_URL);

const api = axios.create({
  baseURL: API_URL,
});

// Add request interceptor for debugging
api.interceptors.request.use(request => {
  console.log('Starting API Request:', request.url);
  return request;
});

// Add response interceptor for debugging
api.interceptors.response.use(
  response => {
    console.log('API Response Success:', response.config.url);
    return response;
  },
  error => {
    console.error('API Response Error:', error.config?.url, error.message);
    return Promise.reject(error);
  }
);

export const uploadDocument = async (file, sourceName, folder, description = '') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_name', sourceName);
  formData.append('folder', folder);
  
  if (description) {
    formData.append('description', description);
  }
  
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const listDocuments = async () => {
  try {
    const response = await api.get('/documents');
    return response.data;
  } catch (error) {
    console.error('List documents error details:', error);
    return []; // Return empty array to prevent UI errors
  }
};

export const deleteDocument = async (docId) => {
  const response = await api.delete(`/documents/${docId}`);
  return response.data;
};

export const askQuestion = async (question, documentIds = null, folder = null, model = "gpt-3.5-turbo") => {
  try {
    console.log(`Asking question - Documents: ${documentIds ? documentIds.length : 0}, Folder: ${folder}, Model: ${model}`);
    
    const payload = {
      question,
      model
    };
    
    if (documentIds && documentIds.length > 0) {
      payload.document_ids = documentIds;
    }
    
    if (folder) {
      payload.folder = folder;
    }
    
    console.log('Sending payload to /ask endpoint:', JSON.stringify(payload, null, 2));
    
    // Add a timeout to prevent hanging requests
    const response = await api.post('/ask', payload, {
      timeout: 30000  // 30 second timeout
    });
    
    // Log the full response for debugging
    console.log('Received answer from API:', JSON.stringify(response.data, null, 2));
    console.log('Answer text:', response.data.answer);
    
    return response.data;
  } catch (error) {
    console.error('Error asking question:', error);
    
    // More specific error handling
    if (error.code === 'ECONNABORTED') {
      throw new Error('The request timed out. This could be due to server load or an issue with the OpenAI API.');
    } else if (error.response) {
      // Server responded with an error status
      const errorMsg = error.response.data?.detail || `Error (${error.response.status}): ${error.response.statusText}`;
      throw new Error(errorMsg);
    } else if (error.request) {
      // Request made but no response received
      throw new Error('No response received from the server. The server may be down or the request timed out.');
    } else {
      // Something else went wrong
      throw new Error(`Error: ${error.message}`);
    }
  }
};

// New folder management functions
export const getFolders = async () => {
  try {
    const response = await api.get('/folders');
    return response.data;
  } catch (error) {
    console.error('Get folders error details:', error);
    return { folders: [], master_bucket: 'unknown' };
  }
};

export const createFolder = async (folderName) => {
  try {
    const formData = new FormData();
    formData.append('folder_name', folderName);
    
    const response = await api.post('/folders', formData);
    return response.data;
  } catch (error) {
    console.error('Create folder error details:', error);
    throw error.response?.data?.detail || error.message || 'Error creating folder';
  }
};

export const deleteFolder = async (folderName) => {
  try {
    const response = await api.delete(`/folders/${folderName}`);
    return response.data;
  } catch (error) {
    console.error('Delete folder error details:', error);
    throw error.response?.data?.detail || error.message || 'Error deleting folder';
  }
};

// Session management functions
export const createSession = async (name, description = '', similarityThreshold = 0.7, customPrompt = '', promptModel = 'gpt-3.5-turbo') => {
  try {
    const response = await api.post('/api/sessions', {
      name,
      description,
      similarity_threshold: similarityThreshold,
      custom_prompt: customPrompt,
      prompt_model: promptModel
    });
    return response.data;
  } catch (error) {
    console.error('Create session error details:', error);
    throw error.response?.data?.detail || error.message || 'Error creating session';
  }
};

export const listSessions = async () => {
  try {
    const response = await api.get('/api/sessions');
    return response.data;
  } catch (error) {
    console.error('List sessions error details:', error);
    return []; // Return empty array to prevent UI errors
  }
};

export const getSession = async (sessionId) => {
  try {
    const response = await api.get(`/api/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error(`Get session ${sessionId} error:`, error);
    throw error.response?.data?.detail || error.message || 'Error retrieving session';
  }
};

export const updateSession = async (sessionId, data) => {
  try {
    const response = await api.put(`/api/sessions/${sessionId}`, {
      ...data,
      // Ensure consistent naming with backend
      similarity_threshold: data.similarityThreshold !== undefined ? data.similarityThreshold : data.similarity_threshold,
      custom_prompt: data.customPrompt !== undefined ? data.customPrompt : data.custom_prompt,
      prompt_model: data.promptModel !== undefined ? data.promptModel : data.prompt_model
    });
    return response.data;
  } catch (error) {
    console.error(`Update session ${sessionId} error:`, error);
    throw error.response?.data?.detail || error.message || 'Error updating session';
  }
};

export const deleteSession = async (sessionId) => {
  try {
    const response = await api.delete(`/api/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error(`Delete session ${sessionId} error:`, error);
    throw error.response?.data?.detail || error.message || 'Error deleting session';
  }
};

export const uploadDocumentToSession = async (sessionId, file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/api/sessions/${sessionId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-Return-Similarity-Logs': 'true',
        'X-Include-Similarity-Method': 'true',
        'X-Include-Detail-Level': 'high'
      },
    });
    
    return response.data;
  } catch (error) {
    console.error(`Upload document to session ${sessionId} error:`, error);
    throw error.response?.data?.detail || error.message || 'Error uploading document to session';
  }
};

export const getSessionDocuments = async (sessionId) => {
  try {
    const response = await api.get(`/api/sessions/${sessionId}/documents`);
    return response.data;
  } catch (error) {
    console.error(`Get session ${sessionId} documents error:`, error);
    throw error.response?.data?.detail || error.message || 'Error retrieving session documents';
  }
};

export const getSessionFolders = async (sessionId) => {
  try {
    const response = await api.get(`/api/sessions/${sessionId}/folders`);
    return response.data;
  } catch (error) {
    console.error(`Get session ${sessionId} folders error:`, error);
    throw error.response?.data?.detail || error.message || 'Error retrieving session folders';
  }
};

export default api; 