import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Slider,
  Tooltip,
  Card,
  CardContent,
  CardActions,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
  Folder as FolderIcon,
  Description as DocumentIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import {
  createSession,
  listSessions,
  deleteSession,
  uploadDocumentToSession,
  getSessionFolders,
  getSessionDocuments,
} from '../services/api';

function SessionManagement() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // New session form state
  const [showSessionForm, setShowSessionForm] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [newSessionDesc, setNewSessionDesc] = useState('');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [creating, setCreating] = useState(false);

  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Upload document dialog state
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadSessionId, setUploadSessionId] = useState(null);
  const [uploadSessionName, setUploadSessionName] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // Session details state
  const [expandedSessionId, setExpandedSessionId] = useState(null);
  const [sessionFolders, setSessionFolders] = useState({});
  const [sessionDocuments, setSessionDocuments] = useState({});
  const [folderLoading, setFolderLoading] = useState(false);

  // Fetch sessions when component mounts
  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listSessions();
      setSessions(data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      setError('Failed to load sessions. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleSessionFormOpen = () => {
    setShowSessionForm(true);
  };

  const handleSessionFormClose = () => {
    setShowSessionForm(false);
    // Reset form fields
    setNewSessionName('');
    setNewSessionDesc('');
    setSimilarityThreshold(0.7);
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!newSessionName.trim()) {
      setError('Please enter a session name');
      return;
    }

    setCreating(true);
    setError('');
    setSuccess('');

    try {
      await createSession(
        newSessionName.trim(),
        newSessionDesc.trim(),
        similarityThreshold
      );
      setSuccess(`Session "${newSessionName}" created successfully`);
      handleSessionFormClose();
      fetchSessions();
    } catch (error) {
      console.error('Error creating session:', error);
      setError(typeof error === 'string' ? error : 'Failed to create session');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteClick = (session) => {
    setSessionToDelete(session);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!sessionToDelete) return;

    setDeleteLoading(true);

    try {
      await deleteSession(sessionToDelete.id);
      setSessions(sessions.filter((s) => s.id !== sessionToDelete.id));
      setDeleteDialogOpen(false);
      setSuccess(`Session "${sessionToDelete.name}" deleted successfully`);
    } catch (error) {
      console.error('Error deleting session:', error);
      setError(typeof error === 'string' ? error : 'Failed to delete session');
    } finally {
      setDeleteLoading(false);
      setSessionToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setSessionToDelete(null);
  };

  const handleUploadClick = (session) => {
    setUploadSessionId(session.id);
    setUploadSessionName(session.name);
    setUploadDialogOpen(true);
  };

  const handleUploadCancel = () => {
    setUploadDialogOpen(false);
    setUploadSessionId(null);
    setUploadSessionName('');
    setFile(null);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError('');

    try {
      await uploadDocumentToSession(uploadSessionId, file);
      setSuccess(`Document "${file.name}" uploaded successfully to session "${uploadSessionName}"`);
      handleUploadCancel();
      
      // Refresh session details if the session is expanded
      if (expandedSessionId === uploadSessionId) {
        fetchSessionDetails(uploadSessionId);
      }
    } catch (error) {
      console.error('Error uploading document:', error);
      setError(typeof error === 'string' ? error : 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleAccordionChange = (sessionId) => async (event, isExpanded) => {
    setExpandedSessionId(isExpanded ? sessionId : null);
    if (isExpanded) {
      await fetchSessionDetails(sessionId);
    }
  };

  const fetchSessionDetails = async (sessionId) => {
    setFolderLoading(true);
    try {
      // Fetch both folders and documents concurrently
      const [foldersResponse, documentsResponse] = await Promise.all([
        getSessionFolders(sessionId),
        getSessionDocuments(sessionId)
      ]);
      
      setSessionFolders(prev => ({ ...prev, [sessionId]: foldersResponse.folders }));
      setSessionDocuments(prev => ({ ...prev, [sessionId]: documentsResponse.documents }));
    } catch (error) {
      console.error('Error fetching session details:', error);
      setError('Failed to load session details');
    } finally {
      setFolderLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Session Management</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleSessionFormOpen}
        >
          Create New Session
        </Button>
      </Box>

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

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : sessions.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No sessions found
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            Create a new session to get started with document organization
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleSessionFormOpen}
            sx={{ mt: 3 }}
          >
            Create New Session
          </Button>
        </Paper>
      ) : (
        <Box>
          {sessions.map((session) => (
            <Accordion
              key={session.id}
              expanded={expandedSessionId === session.id}
              onChange={handleAccordionChange(session.id)}
              sx={{ mb: 2 }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <Typography variant="h6">{session.name}</Typography>
                    <Box>
                      <Chip 
                        label={`${session.document_count} Documents`} 
                        size="small" 
                        sx={{ mr: 1 }}
                      />
                      <Chip 
                        label={`${session.folder_count} Folders`} 
                        size="small" 
                      />
                    </Box>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Created: {formatDate(session.created_at)}
                  </Typography>
                  {session.description && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {session.description}
                    </Typography>
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="subtitle1">
                      Similarity Threshold: {session.similarity_threshold}
                    </Typography>
                    <Box>
                      <Button
                        variant="contained"
                        color="primary"
                        size="small"
                        startIcon={<UploadIcon />}
                        onClick={() => handleUploadClick(session)}
                        sx={{ mr: 1 }}
                      >
                        Upload Document
                      </Button>
                      <Button
                        variant="outlined"
                        color="error"
                        size="small"
                        startIcon={<DeleteIcon />}
                        onClick={() => handleDeleteClick(session)}
                      >
                        Delete Session
                      </Button>
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {folderLoading && expandedSessionId === session.id ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                      <CircularProgress size={30} />
                    </Box>
                  ) : (
                    <>
                      <Typography variant="h6" gutterBottom>
                        Folders
                      </Typography>
                      {sessionFolders[session.id]?.length ? (
                        <Grid container spacing={2}>
                          {sessionFolders[session.id].map((folder) => (
                            <Grid item xs={12} sm={6} md={4} key={folder.folder}>
                              <Card variant="outlined">
                                <CardContent>
                                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                    <FolderIcon color="primary" sx={{ mr: 1 }} />
                                    <Typography variant="subtitle1">
                                      {folder.folder}
                                    </Typography>
                                  </Box>
                                  <Typography variant="body2" color="text.secondary">
                                    {folder.document_count} documents
                                  </Typography>
                                </CardContent>
                                <CardActions>
                                  <Button 
                                    size="small" 
                                    onClick={() => {
                                      // Implement folder view or expand functionality
                                    }}
                                  >
                                    View Documents
                                  </Button>
                                </CardActions>
                              </Card>
                            </Grid>
                          ))}
                        </Grid>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No folders in this session yet. Upload documents to create folders automatically.
                        </Typography>
                      )}
                    </>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}

      {/* Create Session Dialog */}
      <Dialog open={showSessionForm} onClose={handleSessionFormClose} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Session</DialogTitle>
        <form onSubmit={handleCreateSession}>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Session Name"
              type="text"
              fullWidth
              required
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Description (Optional)"
              type="text"
              fullWidth
              multiline
              rows={2}
              value={newSessionDesc}
              onChange={(e) => setNewSessionDesc(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Box sx={{ mb: 2 }}>
              <Typography id="similarity-threshold-slider" gutterBottom>
                Similarity Threshold: {similarityThreshold}
              </Typography>
              <Tooltip title="Documents with similarity scores above this threshold will be grouped together">
                <Slider
                  value={similarityThreshold}
                  onChange={(e, newValue) => setSimilarityThreshold(newValue)}
                  step={0.05}
                  marks
                  min={0.5}
                  max={0.95}
                  valueLabelDisplay="auto"
                  aria-labelledby="similarity-threshold-slider"
                />
              </Tooltip>
              <Typography variant="body2" color="text.secondary">
                Higher values (closer to 1.0) require documents to be more similar to be grouped together
              </Typography>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleSessionFormClose}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={creating}
              startIcon={creating ? <CircularProgress size={20} /> : null}
            >
              {creating ? 'Creating...' : 'Create Session'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete Session Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">Confirm Deletion</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the session "{sessionToDelete?.name}"? This action cannot be undone.
            All documents and folders in this session will be permanently deleted.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            disabled={deleteLoading}
            startIcon={deleteLoading ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {deleteLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Upload Document Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={handleUploadCancel}
        aria-labelledby="upload-dialog-title"
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle id="upload-dialog-title">
          Upload Document to Session: {uploadSessionName}
        </DialogTitle>
        <form onSubmit={handleUploadSubmit}>
          <DialogContent>
            <DialogContentText sx={{ mb: 2 }}>
              The document will be automatically organized into a folder based on its content similarity with existing documents.
            </DialogContentText>
            <Box sx={{ border: '1px dashed grey', borderRadius: 1, p: 2, textAlign: 'center' }}>
              <input
                accept=".pdf,.txt,.md"
                id="contained-button-file"
                type="file"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <label htmlFor="contained-button-file">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<UploadIcon />}
                  sx={{ mb: 2 }}
                >
                  Select File
                </Button>
              </label>
              <Typography variant="body2">
                {file ? `Selected: ${file.name}` : 'No file selected (PDF, TXT, MD)'}
              </Typography>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleUploadCancel}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={uploading || !file}
              startIcon={uploading ? <CircularProgress size={20} /> : null}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}

export default SessionManagement;
