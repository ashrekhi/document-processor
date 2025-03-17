import React, { useState } from 'react';
import axios from 'axios';

const DocumentUploadHelper = ({ onUploadComplete }) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  
  const uploadDocument = async (file, folder) => {
    setUploadStatus('Uploading document...');
    setUploadProgress(10);
    
    const formData = new FormData();
    formData.append('file', file);
    if (folder) {
      formData.append('folder', folder);
    }
    
    try {
      setUploadProgress(30);
      const response = await axios.post('/api/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(Math.min(90, percentCompleted)); // Cap at 90% until we get the response
        }
      });
      
      setUploadProgress(100);
      setUploadStatus('Document uploaded successfully!');
      
      if (onUploadComplete) {
        onUploadComplete(response.data);
      }
      
      return response.data;
    } catch (error) {
      setUploadStatus(`Error uploading document: ${error.message}`);
      console.error('Error uploading document:', error);
      throw error;
    }
  };
  
  return {
    uploadDocument,
    uploadProgress,
    uploadStatus
  };
};

export default DocumentUploadHelper; 