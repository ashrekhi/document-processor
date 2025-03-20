import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Typography,
  Alert,
  Divider,
  LinearProgress,
  Chip,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Collapse,
  Tooltip,
} from '@mui/material';
import {
  Upload as UploadIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
  Article as DocumentIcon,
  GroupWork as SessionIcon,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Code as CodeIcon,
  Calculate as CalculateIcon,
  Timeline as TimelineIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { 
  listSessions, 
  createSession, 
  getSessionDocuments, 
  uploadDocumentToSession 
} from '../services/api';

const DocumentSimilarity = () => {
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState('');
  const [sessionDocuments, setSessionDocuments] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // File upload
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  
  // New session
  const [showNewSession, setShowNewSession] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [creatingSession, setCreatingSession] = useState(false);

  // Similarity logs
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(true);
  const [processingLog, setProcessingLog] = useState(false);

  // Fetch sessions on component mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Fetch session documents when session changes
  useEffect(() => {
    if (selectedSession) {
      fetchSessionDocuments(selectedSession);
    }
  }, [selectedSession]);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const sessionsData = await listSessions();
      setSessions(sessionsData || []);
      
      // Auto-select the first session if available
      if (sessionsData && sessionsData.length > 0 && !selectedSession) {
        setSelectedSession(sessionsData[0].id);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError('Failed to fetch sessions. Please try again.');
      setLoading(false);
    }
  };

  const fetchSessionDocuments = async (sessionId) => {
    try {
      setLoading(true);
      const response = await getSessionDocuments(sessionId);
      setSessionDocuments(response.documents || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching session documents:', err);
      setError('Failed to fetch session documents. Please try again.');
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleFileUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    if (!selectedSession) {
      setError('Please select a session to upload to');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setSuccess(null);
      setProcessingLog(true);
      
      // Show processing message in logs
      const processingLogId = Date.now();
      const initialLog = {
        id: processingLogId,
        timestamp: new Date().toISOString(),
        type: 'processing',
        message: `Processing ${file.name}...`,
        details: {}
      };
      setLogs(prevLogs => [initialLog, ...prevLogs]);
      setProcessingLog(processingLogId);
      
      // Use the uploadDocumentToSession function from our API service
      const uploadData = await uploadDocumentToSession(selectedSession, file);
      
      // Add logs from the response if available
      if (uploadData.similarity_logs) {
        const logs = uploadData.similarity_logs;
        
        // Add log entry for the similarity threshold being used
        if (logs.threshold) {
          addLog({
            type: 'info',
            title: 'Similarity Threshold',
            details: {
              threshold: logs.threshold,
              message: `Using similarity threshold: ${(logs.threshold * 100).toFixed(1)}%`
            },
            timestamp: new Date()
          });
        }
        
        if (logs.comparisons) {
          logs.comparisons.forEach(comparison => {
            addLog({
              type: 'comparison',
              title: `Similarity Comparison`,
              details: {
                score: comparison.similarity,
                documentA: comparison.doc1_name || comparison.doc1_id,
                documentB: comparison.doc2_name || comparison.doc2_id,
                method: comparison.method || 'embedding',
                model: comparison.model || 'default',
                folder: comparison.folder,
                decision: comparison.decision
              },
              timestamp: new Date()
            });
          });
        }
        
        if (logs.folders_checked) {
          addLog({
            type: 'folders',
            title: 'Folders Checked',
            details: logs.folders_checked,
            timestamp: new Date()
          });
        }
        
        if (logs.final_folder) {
          addLog({
            type: 'result',
            title: 'Final Placement',
            details: {
              document: file.name,
              folder: logs.final_folder,
              isNewFolder: logs.is_new_folder,
              reason: logs.placement_reason
            },
            timestamp: new Date()
          });
        }
      } else {
        // Add basic log if detailed logs aren't available
        addLog({
          type: 'success',
          title: 'Document Processed',
          details: `Document uploaded and processed successfully`,
          timestamp: new Date()
        });
      }
      
      setSuccess(`Document "${file.name}" uploaded successfully and organized based on similarity`);
      setFile(null);
      
      // Reset file input
      const fileInput = document.getElementById('file-upload');
      if (fileInput) fileInput.value = '';
      
      // Refresh the document list
      fetchSessionDocuments(selectedSession);
      
      setUploading(false);
      setProcessingLog(false);
    } catch (err) {
      console.error('Error uploading document:', err);
      
      addLog({
        type: 'error',
        title: 'Upload Error',
        details: err.response?.data?.detail || err.message || 'Unknown error occurred',
        timestamp: new Date()
      });
      
      setError(err.response?.data?.detail || 'Failed to upload document. Please try again.');
      setUploading(false);
      setProcessingLog(false);
    }
  };

  const handleCreateSession = async () => {
    if (!newSessionName.trim()) {
      setError('Please enter a session name');
      return;
    }

    try {
      setCreatingSession(true);
      setError(null);
      setSuccess(null);

      await createSession(
        newSessionName.trim(),
        'Created via Document Similarity page',
        similarityThreshold
      );

      setSuccess(`Session "${newSessionName}" created successfully`);
      setNewSessionName('');
      setShowNewSession(false);
      
      // Refresh sessions and select the new one
      await fetchSessions();
      
      setCreatingSession(false);
    } catch (err) {
      console.error('Error creating session:', err);
      setError(err.response?.data?.detail || 'Failed to create session. Please try again.');
      setCreatingSession(false);
    }
  };

  // Add a log entry to the logs array
  const addLog = (log) => {
    setLogs(prevLogs => [log, ...prevLogs].slice(0, 50)); // Keep only the latest 50 logs
  };

  // Clear all logs
  const clearLogs = () => {
    setLogs([]);
  };

  // Group documents by folder
  const documentsByFolder = sessionDocuments.reduce((acc, doc) => {
    const folder = doc.folder || 'Uncategorized';
    if (!acc[folder]) {
      acc[folder] = [];
    }
    acc[folder].push(doc);
    return acc;
  }, {});

  // Format folder name for display
  const formatFolderName = (folder) => {
    if (folder === 'Uncategorized') return folder;
    // Extract number from folder name if it follows pattern "folderX" or "folder_X"
    const match = folder.match(/folder[_-]?(\d+)$/i);
    return match ? `Bucket ${match[1]}` : folder;
  };

  const getFolderColor = (index) => {
    const colors = [
      '#2196f3', // Blue
      '#4caf50', // Green
      '#ff9800', // Orange
      '#9c27b0', // Purple
      '#f44336', // Red
      '#009688', // Teal
    ];
    return colors[index % colors.length];
  };

  // Format similarity score as percentage
  const formatScore = (score) => {
    return `${(score * 100).toFixed(1)}%`;
  };

  // Format timestamp to readable time
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  // Get icon for log type
  const getLogIcon = (type) => {
    switch (type) {
      case 'info':
        return <InfoIcon />;
      case 'success':
        return <CheckIcon color="success" />;
      case 'error':
        return <InfoIcon color="error" />;
      case 'comparison':
        return <CalculateIcon color="primary" />;
      case 'folders':
        return <TimelineIcon color="secondary" />;
      case 'result':
        return <CheckIcon color="success" />;
      default:
        return <InfoIcon />;
    }
  };

  // Render log content based on type
  const renderLogContent = (log) => {
    switch (log.type) {
      case 'comparison':
        return (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Comparing: {log.details.documentA || log.details.doc1_name} ↔️ {log.details.documentB || log.details.doc2_name}
            </Typography>
            <Typography variant="body2">
              <strong>Similarity Score:</strong> {formatScore(log.details.score || log.details.similarity)} 
              <Chip 
                size="small" 
                label={(log.details.score || log.details.similarity) > 0.7 ? "High" : (log.details.score || log.details.similarity) > 0.5 ? "Medium" : "Low"} 
                color={(log.details.score || log.details.similarity) > 0.7 ? "success" : (log.details.score || log.details.similarity) > 0.5 ? "warning" : "error"}
                sx={{ ml: 1 }}
              />
            </Typography>
            <Typography variant="body2">
              <strong>Method:</strong> {log.details.method || "Embedding similarity"}
              {log.details.model && (
                <span> using model: <Chip size="small" label={log.details.model} variant="outlined" sx={{ ml: 1 }} /></span>
              )}
            </Typography>
            <Typography variant="body2">
              <strong>Decision:</strong> {log.details.decision || "Not specified"}
            </Typography>
            <Typography variant="body2">
              <strong>Folder:</strong> {formatFolderName(log.details.folder)}
            </Typography>
          </Box>
        );
      case 'info':
        return (
          <Box>
            <Typography variant="body2">
              {log.details.message || log.message}
            </Typography>
            {log.details.threshold && (
              <Typography variant="body2">
                <strong>Threshold:</strong> {formatScore(log.details.threshold)}
              </Typography>
            )}
            {log.details.reason && (
              <Typography variant="body2">
                <strong>Reason:</strong> {log.details.reason}
              </Typography>
            )}
          </Box>
        );
      case 'success':
        return (
          <Box>
            <Typography variant="body2">
              {log.message}
            </Typography>
            {log.details.folder && (
              <Typography variant="body2">
                <strong>Folder:</strong> {formatFolderName(log.details.folder)}
              </Typography>
            )}
          </Box>
        );
      case 'error':
        return (
          <Box>
            <Typography variant="body2" color="error">
              {log.message}
            </Typography>
          </Box>
        );
      case 'processing':
        return (
          <Box>
            <Typography variant="body2">
              {log.message}
              <CircularProgress size={12} sx={{ ml: 1 }} />
            </Typography>
          </Box>
        );
      case 'result':
        return (
          <Box>
            <Typography variant="body2">
              Document <strong>{log.details.document}</strong> placed in folder:
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              <Chip 
                label={formatFolderName(log.details.folder)} 
                color={log.details.isNewFolder ? "success" : "primary"} 
                size="small" 
                variant={log.details.isNewFolder ? "outlined" : "filled"}
              />
              {log.details.isNewFolder && (
                <Chip 
                  label="New Folder" 
                  color="success" 
                  size="small" 
                  sx={{ ml: 1 }} 
                />
              )}
            </Typography>
            {log.details.reason && (
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                <strong>Reason:</strong> {log.details.reason}
              </Typography>
            )}
          </Box>
        );
      default:
        return (
          <Typography variant="body2">
            {log.message || (typeof log.details === 'string' ? log.details : JSON.stringify(log.details))}
          </Typography>
        );
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" fontWeight="bold" mb={3}>
        Document Organization
      </Typography>
      
      <Grid container spacing={3}>
        {/* Left Side - Upload and Session Select */}
        <Grid item xs={12} md={4}>
          <Paper elevation={0} sx={{ p: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <Typography variant="h6" mb={2}>
              Session & Upload
            </Typography>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}
            
            {success && (
              <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
                {success}
              </Alert>
            )}
            
            {/* Session Selection */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                  Select Session
                </Typography>
                <Button 
                  size="small" 
                  startIcon={<AddIcon />}
                  onClick={() => setShowNewSession(!showNewSession)}
                >
                  New Session
                </Button>
              </Box>
              
              {showNewSession ? (
                <Box sx={{ mb: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                  <TextField
                    fullWidth
                    label="Session Name"
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    size="small"
                    sx={{ mb: 2 }}
                  />
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Typography variant="caption" sx={{ flexGrow: 1 }}>
                      Similarity Threshold: {similarityThreshold}
                    </Typography>
                  </Box>
                  <input
                    type="range"
                    min="0.5"
                    max="0.95"
                    step="0.05"
                    value={similarityThreshold}
                    onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                    style={{ width: '100%' }}
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                    Higher values require documents to be more similar to be grouped together
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => setShowNewSession(false)}
                      sx={{ flexGrow: 1 }}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleCreateSession}
                      disabled={creatingSession || !newSessionName.trim()}
                      sx={{ flexGrow: 1 }}
                    >
                      {creatingSession ? <CircularProgress size={20} /> : 'Create Session'}
                    </Button>
                  </Box>
                </Box>
              ) : (
                <FormControl fullWidth>
                  <InputLabel>Session</InputLabel>
                  <Select
                    value={selectedSession}
                    label="Session"
                    onChange={(e) => setSelectedSession(e.target.value)}
                  >
                    {sessions.map((session) => (
                      <MenuItem key={session.id} value={session.id}>
                        {session.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            {/* Document Upload */}
            <Typography variant="subtitle1" gutterBottom>
              Upload Document
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <input
                id="file-upload"
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <label htmlFor="file-upload">
                <Button
                  variant="outlined"
                  component="span"
                  fullWidth
                  startIcon={<UploadIcon />}
                  sx={{ mb: 1 }}
                >
                  Select File
                </Button>
              </label>
              
              <Typography variant="body2" align="center">
                {file ? file.name : 'No file selected'}
              </Typography>
            </Box>
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleFileUpload}
              disabled={uploading || !file || !selectedSession}
              startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : null}
              fullWidth
            >
              {uploading ? 'Uploading...' : 'Upload & Organize'}
            </Button>
            
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1, textAlign: 'center' }}>
              Documents will be automatically grouped by similarity
            </Typography>
          </Paper>
          
          {selectedSession && sessions.length > 0 && (
            <Paper elevation={0} sx={{ p: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)', mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Session Info
              </Typography>
              
              {loading ? (
                <LinearProgress />
              ) : (
                <Box>
                  <Typography variant="body2">
                    <strong>Name:</strong> {sessions.find(s => s.id === selectedSession)?.name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Similarity Threshold:</strong> {sessions.find(s => s.id === selectedSession)?.similarity_threshold.toFixed(2)}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Document Count:</strong> {sessionDocuments.length}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Folder Count:</strong> {Object.keys(documentsByFolder).length}
                  </Typography>
                </Box>
              )}
            </Paper>
          )}
        </Grid>
        
        {/* Right Side - Documents organized by folders and similarity logs */}
        <Grid item xs={12} md={8}>
          {/* Similarity Logs Panel */}
          <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CodeIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                  Similarity Processing Logs
                </Typography>
              </Box>
              <Box>
                <Tooltip title="Clear Logs">
                  <IconButton size="small" onClick={clearLogs} disabled={logs.length === 0}>
                    <RefreshIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={showLogs ? "Hide Logs" : "Show Logs"}>
                  <IconButton size="small" onClick={() => setShowLogs(!showLogs)}>
                    {showLogs ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            <Collapse in={showLogs}>
              {processingLog && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  <Typography variant="body2">Processing document similarity...</Typography>
                </Box>
              )}
              
              {logs.length === 0 ? (
                <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 3 }}>
                  No logs available. Upload a document to see similarity processing details.
                </Typography>
              ) : (
                <List sx={{ maxHeight: 300, overflowY: 'auto', bgcolor: '#f5f5f5', borderRadius: 1 }}>
                  {logs.map((log, index) => (
                    <ListItem 
                      key={index} 
                      sx={{ 
                        borderBottom: index !== logs.length - 1 ? '1px solid rgba(0,0,0,0.08)' : 'none',
                        py: 1
                      }}
                    >
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        {getLogIcon(log.type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                              {log.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {formatTime(log.timestamp)}
                            </Typography>
                          </Box>
                        }
                        secondary={renderLogContent(log)}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Collapse>
          </Paper>

          {/* Documents by Folder */}
          <Paper elevation={0} sx={{ p: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <Typography variant="h6" mb={2}>
              Documents Organized by Similarity
            </Typography>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : !selectedSession ? (
              <Alert severity="info">
                Please select a session to view documents
              </Alert>
            ) : sessionDocuments.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <DocumentIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography color="text.secondary">
                  No documents found in this session
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Upload documents to see them organized by similarity
                </Typography>
              </Box>
            ) : (
              <Box>
                {Object.entries(documentsByFolder).map(([folder, docs], folderIndex) => (
                  <Box key={folder} sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box 
                        sx={{ 
                          width: 16, 
                          height: 16, 
                          borderRadius: '50%', 
                          bgcolor: getFolderColor(folderIndex),
                          mr: 1
                        }} 
                      />
                      <Typography variant="subtitle1" fontWeight="bold">
                        {formatFolderName(folder)}
                      </Typography>
                      <Chip 
                        label={`${docs.length} ${docs.length === 1 ? 'document' : 'documents'}`} 
                        size="small" 
                        sx={{ ml: 1 }} 
                      />
                    </Box>
                    
                    <Grid container spacing={2}>
                      {docs.map((doc) => (
                        <Grid item xs={12} sm={6} md={4} key={doc.id}>
                          <Card 
                            variant="outlined" 
                            sx={{ 
                              height: '100%', 
                              borderLeft: `4px solid ${getFolderColor(folderIndex)}`,
                              transition: 'transform 0.2s',
                              '&:hover': {
                                transform: 'translateY(-4px)',
                                boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
                              }
                            }}
                          >
                            <CardContent>
                              <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                                <DocumentIcon sx={{ mr: 1, color: 'text.secondary' }} />
                                <Box>
                                  <Typography variant="subtitle2" noWrap>
                                    {doc.filename || 'Unnamed Document'}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {new Date(doc.created_at).toLocaleDateString()}
                                  </Typography>
                                </Box>
                              </Box>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DocumentSimilarity;
