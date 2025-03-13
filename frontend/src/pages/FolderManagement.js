import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { getFolders, createFolder, deleteFolder } from '../services/api';

function FolderManagement() {
  const [folders, setFolders] = useState([]);
  const [masterBucket, setMasterBucket] = useState('');
  const [newFolderName, setNewFolderName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [folderToDelete, setFolderToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const fetchFolders = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await getFolders();
      setFolders(data.folders);
      setMasterBucket(data.master_bucket);
    } catch (error) {
      console.error('Error fetching folders:', error);
      setError('Failed to load folders. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFolders();
  }, []);

  const handleCreateFolder = async (event) => {
    event.preventDefault();
    
    if (!newFolderName) {
      setError('Please enter a folder name');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await createFolder(newFolderName);
      setSuccess(`Folder ${newFolderName} created successfully`);
      setNewFolderName('');
      fetchFolders();
    } catch (error) {
      console.error('Error creating folder:', error);
      setError(error.response?.data?.detail || 'Error creating folder');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (folder) => {
    setFolderToDelete(folder);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!folderToDelete) return;
    
    setDeleteLoading(true);
    
    try {
      await deleteFolder(folderToDelete);
      setSuccess(`Folder ${folderToDelete} deleted successfully`);
      setFolders(folders.filter(f => f !== folderToDelete));
      setDeleteDialogOpen(false);
    } catch (error) {
      console.error('Error deleting folder:', error);
      setError(error.response?.data?.detail || 'Error deleting folder');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setFolderToDelete(null);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Folder Management
      </Typography>
      
      <Typography variant="subtitle1" gutterBottom>
        Master Bucket: {masterBucket}
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}
      
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
        <Paper elevation={2} sx={{ p: 3, flex: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Available Folders
            </Typography>
            <Button 
              startIcon={<RefreshIcon />} 
              onClick={fetchFolders}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          ) : folders.length === 0 ? (
            <Alert severity="info">
              No folders found.
            </Alert>
          ) : (
            <List>
              {folders.map((folder) => (
                <ListItem key={folder} divider>
                  <ListItemText 
                    primary={folder} 
                    secondary={folder === 'metadata' ? 'System Folder' : ''}
                  />
                  <ListItemSecondaryAction>
                    <IconButton 
                      edge="end" 
                      color="error"
                      onClick={() => handleDeleteClick(folder)}
                      disabled={folder === 'metadata' || folder === 'documents'}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}
        </Paper>
        
        <Paper elevation={2} sx={{ p: 3, flex: 1 }}>
          <Typography variant="h6" gutterBottom>
            Create New Folder
          </Typography>
          
          <form onSubmit={handleCreateFolder}>
            <TextField
              label="Folder Name"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              fullWidth
              required
              margin="normal"
              helperText="Enter a name for the new folder"
            />
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <AddIcon />}
              >
                Create Folder
              </Button>
            </Box>
          </form>
        </Paper>
      </Box>
      
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Folder</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the folder "{folderToDelete}"? This action cannot be undone and will delete all files within the folder.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={deleteLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            disabled={deleteLoading}
            startIcon={deleteLoading && <CircularProgress size={20} />}
          >
            {deleteLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default FolderManagement; 