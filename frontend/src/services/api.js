import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadDocument = async (file, sourceName, description) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_name', sourceName);
  
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
  const response = await api.get('/documents');
  return response.data;
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

export default api; 