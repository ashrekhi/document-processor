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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';
import { uploadDocument, getFolders } from '../services/api';

// Define core folders that should be hidden from the UI
const CORE_FOLDERS = ['metadata', 'documents'];

function DocumentUpload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [folder, setFolder] = useState('');
  const [description, setDescription] = useState('');
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchFolders();
  }, []);

  const fetchFolders = async () => {
    setLoading(true);
    try {
      const data = await getFolders();
      // Filter out core folders that should be hidden
      const filteredFolders = (data.folders || []).filter(
        folder => !CORE_FOLDERS.includes(folder)
      );
      setFolders(filteredFolders);
      
      // If there's at least one folder, select it by default
      if (filteredFolders.length > 0 && !folder) {
        setFolder(filteredFolders[0]);
      }
    } catch (error) {
      console.error('Error fetching folders:', error);
      setError('Failed to load folders. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file to upload');
      return;
    }
    
    if (!folder) {
      setError('Please select a folder');
      return;
    }
    
    setUploading(true);
    setError('');
    setSuccess('');
    
    try {
      // Use the folder name as the source name
      await uploadDocument(file, folder, folder, description);
      setSuccess(`Document "${fileName}" uploaded successfully to ${folder}`);
      
      // Reset form
      setFile(null);
      setFileName('');
      setDescription('');
      document.getElementById('file-upload').value = '';
      
      // Redirect to documents list after 2 seconds
      setTimeout(() => {
        navigate('/documents');
      }, 2000);
    } catch (error) {
      console.error('Error uploading document:', error);
      setError(typeof error === 'string' ? error : 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Document
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}
      
      <Paper elevation={2} sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Box sx={{ mb: 3 }}>
            <Button
              variant="contained"
              component="label"
              startIcon={<UploadIcon />}
              fullWidth
            >
              Select File
              <input
                id="file-upload"
                type="file"
                accept=".pdf,.txt,.md"
                hidden
                onChange={handleFileChange}
              />
            </Button>
            {fileName && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Selected file: {fileName}
              </Typography>
            )}
          </Box>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Folder</InputLabel>
            <Select
              value={folder}
              onChange={(e) => setFolder(e.target.value)}
              required
              disabled={loading || folders.length === 0}
            >
              {loading ? (
                <MenuItem disabled>Loading folders...</MenuItem>
              ) : folders.length === 0 ? (
                <MenuItem disabled>No folders available</MenuItem>
              ) : (
                folders.map((f) => (
                  <MenuItem key={f} value={f}>
                    {f}
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>
          
          <TextField
            label="Description (Optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
            multiline
            rows={3}
            margin="normal"
            helperText="Enter a description for this document"
          />
          
          <Box sx={{ mt: 3 }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={uploading || !file || !folder}
              fullWidth
              startIcon={uploading && <CircularProgress size={20} />}
            >
              {uploading ? 'Uploading...' : 'Upload Document'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
}

export default DocumentUpload; 