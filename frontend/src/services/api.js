import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
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

export const uploadDocument = async (file, sourceName, description) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_name', sourceName);
  
  if (description) {
    formData.append('description', description);
  }
  
  try {
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Upload document error details:', error);
    throw error.response?.data?.detail || error.message || 'Error uploading document';
  }
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

export const askQuestion = async (question, documentIds) => {
  const response = await api.post('/ask', {
    question,
    document_ids: documentIds,
  });
  
  return response.data;
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

export default api; 