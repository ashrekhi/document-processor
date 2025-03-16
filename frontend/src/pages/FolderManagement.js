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
import { Add as AddIcon, Delete as DeleteIcon, Folder as FolderIcon } from '@mui/icons-material';
import { getFolders, createFolder, deleteFolder } from '../services/api';

function FolderManagement() {
  const [folders, setFolders] = useState([]);
  const [masterBucket, setMasterBucket] = useState('');
  const [newFolderName, setNewFolderName] = useState('');
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [folderToDelete, setFolderToDelete] = useState('');
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
    
    setCreating(true);
    setError('');
    setSuccess('');
    
    try {
      await createFolder(newFolderName.trim());
      setSuccess(`Folder "${newFolderName}" created successfully`);
      setNewFolderName('');
      fetchFolders();
    } catch (error) {
      console.error('Error creating folder:', error);
      setError(typeof error === 'string' ? error : 'Failed to create folder');
    } finally {
      setCreating(false);
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
      setFolders(folders.filter(f => f !== folderToDelete));
      setDeleteDialogOpen(false);
      setSuccess(`Folder "${folderToDelete}" deleted successfully`);
    } catch (error) {
      console.error('Error deleting folder:', error);
      setError(typeof error === 'string' ? error : 'Failed to delete folder');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setFolderToDelete('');
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Folder Management
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
      
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Create New Folder
        </Typography>
        
        <form onSubmit={handleCreateFolder}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <TextField
              label="Folder Name"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              fullWidth
              required
              margin="normal"
              helperText="Enter a name for the new folder"
            />
            
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={creating}
              startIcon={creating ? <CircularProgress size={20} /> : <AddIcon />}
              sx={{ mt: 2, height: 56 }}
            >
              {creating ? 'Creating...' : 'Create Folder'}
            </Button>
          </Box>
        </form>
      </Paper>
      
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Available Folders
        </Typography>
        
        {masterBucket && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Master Bucket: {masterBucket}
          </Typography>
        )}
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : folders.length === 0 ? (
          <Typography variant="body1" color="text.secondary" sx={{ p: 2 }}>
            No folders found. Create a folder to get started.
          </Typography>
        ) : (
          <List>
            {folders.map((folder) => (
              <React.Fragment key={folder}>
                <ListItem>
                  <FolderIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <ListItemText 
                    primary={folder} 
                    secondary={`s3://${masterBucket}/${folder}/`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      color="error"
                      onClick={() => handleDeleteClick(folder)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>
      
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Folder</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the folder "{folderToDelete}"? This will delete all files within this folder and cannot be undone.
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