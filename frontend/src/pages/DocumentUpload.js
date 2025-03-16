import React, { useState, useEffect } from 'react';
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
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  FormHelperText,
} from '@mui/material';
import { CloudUpload as UploadIcon, Folder as FolderIcon } from '@mui/icons-material';
import { uploadDocument, getFolders } from '../services/api';

function DocumentUpload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [sourceName, setSourceName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [folders, setFolders] = useState([]);
  const [foldersLoading, setFoldersLoading] = useState(true);

  useEffect(() => {
    const fetchFolders = async () => {
      setFoldersLoading(true);
      try {
        const data = await getFolders();
        setFolders(data.folders || []);
      } catch (error) {
        console.error('Error fetching folders:', error);
      } finally {
        setFoldersLoading(false);
      }
    };

    fetchFolders();
  }, []);

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
      setError('Please select a folder');
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
      
      // Redirect to documents list after 2 seconds
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
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <AlertTitle>Success</AlertTitle>
          Document uploaded successfully! Redirecting to documents list...
        </Alert>
      )}
      
      <Paper elevation={2} sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Box sx={{ mb: 3 }}>
            <Button
              variant="contained"
              component="label"
              fullWidth
              sx={{ p: 2, border: '1px dashed grey', bgcolor: 'background.paper' }}
            >
              {file ? file.name : 'Select File'}
              <input
                type="file"
                hidden
                onChange={handleFileChange}
                accept=".pdf,.txt,.md"
              />
            </Button>
            <Typography variant="caption" color="text.secondary">
              Supported file types: PDF, TXT, MD
            </Typography>
          </Box>
          
          <FormControl fullWidth margin="normal" required>
            <InputLabel id="folder-select-label">Folder</InputLabel>
            <Select
              labelId="folder-select-label"
              value={sourceName}
              onChange={(e) => setSourceName(e.target.value)}
              label="Folder"
              disabled={foldersLoading}
              startAdornment={<FolderIcon sx={{ mr: 1, ml: -0.5 }} />}
            >
              {foldersLoading ? (
                <MenuItem disabled>Loading folders...</MenuItem>
              ) : folders.length === 0 ? (
                <MenuItem disabled>No folders available</MenuItem>
              ) : (
                folders.map((folder) => (
                  <MenuItem key={folder} value={folder}>
                    {folder}
                  </MenuItem>
                ))
              )}
            </Select>
            <FormHelperText>
              {folders.length === 0 && !foldersLoading ? 
                "Please create a folder in Folder Management first" : 
                "Select a folder to store this document"}
            </FormHelperText>
          </FormControl>
          
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
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {folders.length === 0 && !foldersLoading && (
              <Button
                variant="outlined"
                color="primary"
                onClick={() => navigate('/folders')}
              >
                Create Folder
              </Button>
            )}
            <Box sx={{ flex: 1 }} />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={loading || folders.length === 0}
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