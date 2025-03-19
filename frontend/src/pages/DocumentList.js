import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Button,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Grid,
  Divider
} from '@mui/material';
import { 
  Delete as DeleteIcon, 
  Description as DescriptionIcon, 
  Folder as FolderIcon
} from '@mui/icons-material';
import { listDocuments, deleteDocument } from '../services/api';

function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [documentsByFolder, setDocumentsByFolder] = useState({});
  const [selectedFolder, setSelectedFolder] = useState(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await listDocuments();
      setDocuments(data);
      
      // Group documents by folder
      const groupedDocs = {};
      data.forEach(doc => {
        const folder = doc.folder || 'Uncategorized';
        if (!groupedDocs[folder]) {
          groupedDocs[folder] = [];
        }
        groupedDocs[folder].push(doc);
      });
      
      setDocumentsByFolder(groupedDocs);
      
      // Select first folder by default
      const folders = Object.keys(groupedDocs);
      if (folders.length > 0) {
        setSelectedFolder(folders[0]);
      }
      
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError('Failed to load documents. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDeleteClick = (document) => {
    setDocumentToDelete(document);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!documentToDelete) return;
    
    setDeleteLoading(true);
    
    try {
      await deleteDocument(documentToDelete.id);
      
      // Update documents state
      setDocuments(documents.filter(doc => doc.id !== documentToDelete.id));
      
      // Update grouped documents state
      const folder = documentToDelete.folder || 'Uncategorized';
      const updatedGroupedDocs = { ...documentsByFolder };
      updatedGroupedDocs[folder] = updatedGroupedDocs[folder].filter(
        doc => doc.id !== documentToDelete.id
      );
      
      // Remove folder if empty
      if (updatedGroupedDocs[folder].length === 0) {
        delete updatedGroupedDocs[folder];
        
        // If current folder was deleted, select first available folder
        if (folder === selectedFolder) {
          const remainingFolders = Object.keys(updatedGroupedDocs);
          setSelectedFolder(remainingFolders.length > 0 ? remainingFolders[0] : null);
        }
      }
      
      setDocumentsByFolder(updatedGroupedDocs);
      setDeleteDialogOpen(false);
      
    } catch (error) {
      console.error('Error deleting document:', error);
      setError('Failed to delete document. Please try again later.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setDocumentToDelete(null);
  };
  
  const handleFolderSelect = (folder) => {
    setSelectedFolder(folder);
  };

  const folders = Object.keys(documentsByFolder).sort();
  const hasDocuments = folders.length > 0;
  const currentFolderDocuments = selectedFolder ? documentsByFolder[selectedFolder] || [] : [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Documents
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : !hasDocuments ? (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No documents found. Upload a document to get started.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            href="/upload"
            sx={{ mt: 2 }}
          >
            Upload Document
          </Button>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {/* Folder list */}
          <Grid item xs={12} md={3}>
            <Paper sx={{ height: '100%', maxHeight: '75vh', overflow: 'auto' }}>
              <List component="nav" aria-label="folders">
                {folders.map((folder) => (
                  <ListItem 
                    button 
                    key={folder}
                    selected={selectedFolder === folder}
                    onClick={() => handleFolderSelect(folder)}
                    sx={{
                      bgcolor: selectedFolder === folder ? 'primary.light' : 'inherit',
                      '&:hover': { bgcolor: selectedFolder === folder ? 'primary.light' : 'rgba(0, 0, 0, 0.04)' }
                    }}
                  >
                    <ListItemIcon>
                      <FolderIcon color={selectedFolder === folder ? 'primary' : 'inherit'} />
                    </ListItemIcon>
                    <ListItemText 
                      primary={`${folder} (${documentsByFolder[folder].length})`} 
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
          
          {/* Document list */}
          <Grid item xs={12} md={9}>
            <Paper sx={{ height: '100%', maxHeight: '75vh', overflow: 'auto' }}>
              {selectedFolder && (
                <>
                  <Box sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                    <Typography variant="h6">
                      <FolderIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                      {selectedFolder}
                    </Typography>
                  </Box>
                  <Divider />
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Filename</TableCell>
                          <TableCell>Source</TableCell>
                          <TableCell>Description</TableCell>
                          <TableCell align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {currentFolderDocuments.map((document) => (
                          <TableRow key={document.id}>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <DescriptionIcon fontSize="small" sx={{ mr: 1, color: 'primary.main' }} />
                                {document.filename}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Chip label={document.source} size="small" />
                            </TableCell>
                            <TableCell>{document.description || '-'}</TableCell>
                            <TableCell align="right">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDeleteClick(document)}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}
      
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Document</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{documentToDelete?.filename}"?
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
          >
            {deleteLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default DocumentList; 