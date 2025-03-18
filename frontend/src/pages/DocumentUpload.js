import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  CircularProgress,
  Divider,
  alpha,
  Paper
} from '@mui/material';
import { 
  CloudUpload as UploadIcon, 
  Description as DocumentIcon,
  UploadFile as UploadFileIcon,
  Folder as FolderIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { uploadDocument, getFolders } from '../services/api';
import { 
  PageHeader, 
  SectionContainer, 
  StyledTextField, 
  PrimaryButton,
  TitledDivider,
  EmptyState,
  LoadingIndicator
} from '../components/StyledComponents';

// Define core folders that should be hidden from the UI
const CORE_FOLDERS = ['metadata', 'documents'];

// FileUploader component for drag and drop functionality
const FileUploader = ({ onFileSelected, selectedFileName }) => {
  const [isDragging, setIsDragging] = useState(false);
  
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      // Check if the file extension is valid
      const validExtensions = ['.pdf', '.txt', '.md'];
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
      
      if (validExtensions.includes(fileExtension)) {
        onFileSelected(file);
      }
    }
  };
  
  return (
    <Box
      sx={{
        border: '2px dashed',
        borderColor: (theme) => isDragging 
          ? theme.palette.primary.main 
          : selectedFileName 
            ? theme.palette.success.light 
            : theme.palette.divider,
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        backgroundColor: (theme) => isDragging 
          ? alpha(theme.palette.primary.main, 0.05) 
          : selectedFileName 
            ? alpha(theme.palette.success.main, 0.05) 
            : theme.palette.background.paper,
        transition: 'all 0.2s ease-in-out',
        cursor: 'pointer',
      }}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={() => document.getElementById('file-upload').click()}
    >
      {selectedFileName ? (
        <Box>
          <DocumentIcon 
            color="success" 
            sx={{ fontSize: 48, mb: 2 }} 
          />
          <Typography variant="subtitle1" fontWeight={600}>
            {selectedFileName}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Click or drag to replace
          </Typography>
        </Box>
      ) : (
        <Box>
          <UploadFileIcon 
            color="primary" 
            sx={{ fontSize: 48, mb: 2, opacity: isDragging ? 1 : 0.7 }} 
          />
          <Typography variant="subtitle1" fontWeight={600}>
            {isDragging ? 'Drop your file here' : 'Drag & Drop your file here'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            or click to browse (PDF, TXT, MD)
          </Typography>
        </Box>
      )}
      <input
        id="file-upload"
        type="file"
        accept=".pdf,.txt,.md"
        hidden
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            onFileSelected(e.target.files[0]);
          }
        }}
      />
    </Box>
  );
};

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

  const handleFileChange = (selectedFile) => {
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
      <PageHeader 
        title="Upload Document" 
        subtitle="Upload a new document to process with RAG technology"
      />
      
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3, borderRadius: 2 }} 
          onClose={() => setError('')}
        >
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert 
          severity="success" 
          sx={{ mb: 3, borderRadius: 2 }} 
          onClose={() => setSuccess('')}
        >
          {success}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <SectionContainer>
            <form onSubmit={handleSubmit}>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Document Information
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Upload a document (PDF, TXT, or MD) to be processed by our RAG system.
              </Typography>
              
              <TitledDivider title="File Selection" />
              
              <Box sx={{ mb: 4 }}>
                <FileUploader 
                  onFileSelected={handleFileChange} 
                  selectedFileName={fileName} 
                />
              </Box>
              
              <TitledDivider title="Document Details" />
              
              <FormControl fullWidth margin="normal" sx={{ mb: 3 }}>
                <InputLabel>Folder</InputLabel>
                <Select
                  value={folder}
                  onChange={(e) => setFolder(e.target.value)}
                  required
                  disabled={loading || folders.length === 0}
                  sx={{ borderRadius: 2 }}
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
              
              <StyledTextField
                label="Description (Optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                fullWidth
                multiline
                rows={3}
                margin="normal"
                helperText="Enter a description for this document"
                sx={{ mb: 3 }}
              />
              
              <PrimaryButton
                type="submit"
                disabled={uploading || !file || !folder}
                fullWidth
                size="large"
                startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <UploadIcon />}
              >
                {uploading ? 'Uploading...' : 'Upload Document'}
              </PrimaryButton>
            </form>
          </SectionContainer>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper 
            sx={{ 
              p: 3, 
              borderRadius: 3,
              height: '100%',
              backgroundImage: (theme) => `radial-gradient(${alpha(theme.palette.primary.main, 0.15)} 1px, transparent 0)`,
              backgroundSize: '20px 20px',
              backgroundPosition: '-19px -19px',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <InfoIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" fontWeight={600}>
                Upload Tips
              </Typography>
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                Supported Formats
              </Typography>
              <Typography variant="body2" paragraph>
                PDF (.pdf), Text (.txt), and Markdown (.md) files are supported.
              </Typography>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                File Organization
              </Typography>
              <Typography variant="body2" paragraph>
                Choose the appropriate folder to organize your documents. This helps with better categorization and searching.
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                Processing Time
              </Typography>
              <Typography variant="body2">
                Larger documents may take longer to process. You will be redirected to the documents page once the upload is complete.
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default DocumentUpload; 