import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  AlertTitle,
} from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';
import { uploadDocument } from '../services/api';

function DocumentUpload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [sourceName, setSourceName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!file) {
      setError('Please select a file to upload');
      return;
    }
    
    if (!sourceName) {
      setError('Please enter a source name');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await uploadDocument(file, sourceName, description);
      setSuccess(true);
      
      // Reset form
      setFile(null);
      setSourceName('');
      setDescription('');
      
      // Redirect to documents page after 2 seconds
      setTimeout(() => {
        navigate('/documents');
      }, 2000);
    } catch (error) {
      console.error('Error uploading document:', error);
      setError(error.response?.data?.detail || 'Error uploading document');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Document
      </Typography>
      
      <Paper elevation={2} sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
        {success ? (
          <Alert severity="success" sx={{ mb: 3 }}>
            <AlertTitle>Success</AlertTitle>
            Document uploaded successfully! Redirecting to documents page...
          </Alert>
        ) : null}
        
        {error ? (
          <Alert severity="error" sx={{ mb: 3 }}>
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        ) : null}
        
        <form onSubmit={handleSubmit}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Select Document
            </Typography>
            <Button
              variant="outlined"
              component="label"
              startIcon={<UploadIcon />}
              fullWidth
            >
              {file ? file.name : 'Choose File'}
              <input
                type="file"
                hidden
                onChange={handleFileChange}
                accept=".pdf,.txt,.md"
              />
            </Button>
            <Typography variant="caption" color="text.secondary">
              Supported formats: PDF, TXT, MD
            </Typography>
          </Box>
          
          <TextField
            label="Source Name"
            value={sourceName}
            onChange={(e) => setSourceName(e.target.value)}
            fullWidth
            required
            margin="normal"
            helperText="Enter a name for the source of this document"
          />
          
          <TextField
            label="Description (Optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
            margin="normal"
            multiline
            rows={3}
            helperText="Enter a description for this document"
          />
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
            >
              {loading ? 'Uploading...' : 'Upload Document'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
}

export default DocumentUpload; 