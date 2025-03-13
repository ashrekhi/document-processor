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
  FormControlLabel,
  Switch,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { getBuckets, createBucket, deleteBucket } from '../services/api';

function BucketManagement() {
  const [buckets, setBuckets] = useState([]);
  const [metadataBucket, setMetadataBucket] = useState('');
  const [newBucketName, setNewBucketName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [bucketToDelete, setBucketToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [forceDelete, setForceDelete] = useState(false);

  const fetchBuckets = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await getBuckets();
      setBuckets(data.available_buckets);
      setMetadataBucket(data.metadata_bucket);
    } catch (error) {
      console.error('Error fetching buckets:', error);
      setError('Failed to load buckets. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBuckets();
  }, []);

  const handleCreateBucket = async (event) => {
    event.preventDefault();
    
    if (!newBucketName) {
      setError('Please enter a bucket name');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await createBucket(newBucketName);
      setSuccess(`Bucket ${newBucketName} created successfully`);
      setNewBucketName('');
      fetchBuckets();
    } catch (error) {
      console.error('Error creating bucket:', error);
      setError(error.response?.data?.detail || 'Error creating bucket');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (bucket) => {
    setBucketToDelete(bucket);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!bucketToDelete) return;
    
    setDeleteLoading(true);
    
    try {
      await deleteBucket(bucketToDelete, forceDelete);
      setSuccess(`Bucket ${bucketToDelete} deleted successfully`);
      setBuckets(buckets.filter(b => b !== bucketToDelete));
      setDeleteDialogOpen(false);
    } catch (error) {
      console.error('Error deleting bucket:', error);
      setError(error.response?.data?.detail || 'Error deleting bucket');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setBucketToDelete(null);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        S3 Bucket Management
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
              Available Buckets
            </Typography>
            <Button 
              startIcon={<RefreshIcon />} 
              onClick={fetchBuckets}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          ) : buckets.length === 0 ? (
            <Alert severity="info">
              No buckets found.
            </Alert>
          ) : (
            <List>
              {buckets.map((bucket) => (
                <ListItem key={bucket} divider>
                  <ListItemText 
                    primary={bucket} 
                    secondary={bucket === metadataBucket ? 'Metadata Bucket' : ''}
                  />
                  <ListItemSecondaryAction>
                    <IconButton 
                      edge="end" 
                      color="error"
                      onClick={() => handleDeleteClick(bucket)}
                      disabled={bucket === metadataBucket}
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
            Create New Bucket
          </Typography>
          
          <form onSubmit={handleCreateBucket}>
            <TextField
              label="Bucket Name"
              value={newBucketName}
              onChange={(e) => setNewBucketName(e.target.value)}
              fullWidth
              required
              margin="normal"
              helperText="Bucket names must be globally unique, 3-63 characters, lowercase, and can contain numbers and hyphens"
            />
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <AddIcon />}
              >
                Create Bucket
              </Button>
            </Box>
          </form>
        </Paper>
      </Box>
      
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Bucket</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the bucket "{bucketToDelete}"? This action cannot be undone.
          </DialogContentText>
          <FormControlLabel
            control={
              <Switch
                checked={forceDelete}
                onChange={(e) => setForceDelete(e.target.checked)}
              />
            }
            label="Force delete (ignore errors)"
          />
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

export default BucketManagement; 