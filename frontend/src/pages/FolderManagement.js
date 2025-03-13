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
      setFolders(data.folders || []);
      setMasterBucket(data.master_bucket || '');
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

  const handleCreateFolder = async (e) => {
    e.preventDefault();
    
    if (!newFolderName.trim()) {
      setError('Please enter a folder name');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await createFolder(newFolderName);
      setSuccess(`Folder "${newFolderName}" created successfully`);
      setNewFolderName('');
      fetchFolders();
    } catch (error) {
      console.error('Error creating folder:', error);
      // Convert error object to string if it's an object
      const errorMessage = typeof error === 'object' ? 
        (error.message || JSON.stringify(error)) : 
        String(error);
      setError(`Failed to create folder: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (folderName) => {
    setFolderToDelete(folderName);
    setDeleteDialogOpen(true);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setFolderToDelete(null);
  };

  const handleDeleteConfirm = async () => {
    if (!folderToDelete) return;
    
    setDeleteLoading(true);
    
    try {
      await deleteFolder(folderToDelete);
      setSuccess(`Folder "${folderToDelete}" deleted successfully`);
      fetchFolders();
    } catch (error) {
      console.error('Error deleting folder:', error);
      // Convert error object to string if it's an object
      const errorMessage = typeof error === 'object' ? 
        (error.message || JSON.stringify(error)) : 
        String(error);
      setError(`Failed to delete folder: ${errorMessage}`);
    } finally {
      setDeleteLoading(false);
      setDeleteDialogOpen(false);
      setFolderToDelete(null);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Folder Management
      </Typography>
      
      {error && typeof error === 'string' && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}
      
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">
          Master Bucket: {masterBucket}
        </Typography>
        
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchFolders}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>
      
      <Paper elevation={2} sx={{ mb: 4 }}>
        <List>
          {loading && folders.length === 0 ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : folders.length === 0 ? (
            <ListItem>
              <ListItemText primary="No folders found" />
            </ListItem>
          ) : (
            folders.map((folder, index) => (
              <React.Fragment key={folder}>
                {index > 0 && <Divider />}
                <ListItem>
                  <ListItemText
                    primary={folder}
                    secondary={`s3://${masterBucket}/${folder}/`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      aria-label="delete"
                      onClick={() => handleDeleteClick(folder)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              </React.Fragment>
            ))
          )}
        </List>
      </Paper>
      
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Create New Folder
        </Typography>
        
        <Paper elevation={2} sx={{ p: 3 }}>
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