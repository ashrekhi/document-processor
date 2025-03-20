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
  FormHelperText,
  Slider,
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
  uploadDocumentToSession,
  updateSession
} from '../services/api';

// Available LLM models
const availableModels = [
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' }
];

// Reusable component for prompt and model selection
const PromptModelSelector = ({ 
  customPrompt, 
  setCustomPrompt, 
  promptModel, 
  setPromptModel, 
  size = "small",
  rows = 2
}) => {
  return (
    <Box>
      <TextField
        fullWidth
        label="Custom Prompt (Optional)"
        placeholder="Instructions to clean document text (e.g., Remove headers and footers)"
        value={customPrompt}
        onChange={(e) => setCustomPrompt(e.target.value)}
        multiline
        rows={rows}
        size={size}
        sx={{ mb: 1 }}
        helperText="The prompt will be applied to preprocess document text before similarity matching"
      />
      <FormControl fullWidth size={size} sx={{ mb: 2 }}>
        <InputLabel id="prompt-model-label">Prompt Model</InputLabel>
        <Select
          labelId="prompt-model-label"
          value={promptModel}
          label="Prompt Model"
          onChange={(e) => setPromptModel(e.target.value)}
          disabled={!customPrompt.trim()}
        >
          {availableModels.map((model) => (
            <MenuItem key={model.value} value={model.value}>
              {model.label}
            </MenuItem>
          ))}
        </Select>
        <FormHelperText>Select the LLM to use for text processing in this session</FormHelperText>
      </FormControl>
    </Box>
  );
};

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
  const [customPrompt, setCustomPrompt] = useState('');
  const [promptModel, setPromptModel] = useState('gpt-3.5-turbo');
  const fileInputRef = React.useRef(null);
  
  // New session
  const [showNewSession, setShowNewSession] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [newSessionCustomPrompt, setNewSessionCustomPrompt] = useState('');
  const [newSessionPromptModel, setNewSessionPromptModel] = useState('gpt-3.5-turbo');
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
      
      // Set custom prompt and model from the selected session
      const session = sessions.find(s => s.id === selectedSession);
      if (session) {
        setCustomPrompt(session.custom_prompt || '');
        setPromptModel(session.prompt_model || 'gpt-3.5-turbo');
      }
    }
  }, [selectedSession, sessions]);

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

  const triggerFileInput = () => {
    fileInputRef.current.click();
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
      
      // Get the current session data to update its custom prompt if needed
      const currentSession = sessions.find(s => s.id === selectedSession);
      
      // Always update session with the current prompt and model values
      // This ensures the session metadata stays in sync with what the user sees
      if (currentSession && 
          (currentSession.custom_prompt !== customPrompt.trim() || 
           currentSession.prompt_model !== promptModel)) {
        try {
          // Update the session with the new custom prompt and model
          await updateSession(selectedSession, {
            ...currentSession,
            custom_prompt: customPrompt.trim(),
            prompt_model: promptModel
          });
          
          // Add a log about the custom prompt and model
          addLog({
            type: 'info',
            title: 'Custom Prompt Updated',
            details: {
              message: customPrompt.trim() 
                ? `Using custom prompt with model ${promptModel}: ${customPrompt.trim()}`
                : `Using no custom prompt for preprocessing`
            },
            timestamp: new Date()
          });
          
          // Refresh sessions to get updated data
          await fetchSessions();
        } catch (err) {
          console.error('Error updating session with custom prompt:', err);
        }
      }
      
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

      // Include the model in the session data
      await createSession(
        newSessionName.trim(),
        'Created via Document Similarity page',
        similarityThreshold,
        newSessionCustomPrompt.trim(),
        newSessionPromptModel
      );

      setSuccess(`Session "${newSessionName}" created successfully`);
      setNewSessionName('');
      setNewSessionCustomPrompt('');
      setNewSessionPromptModel('gpt-3.5-turbo');
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
    switch(type) {
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
                {/* Add clarification for threshold comparison if needed */}
                {log.details.reason && log.details.reason.includes("below threshold") && (
                  <span> (Documents with similarity score ≥ threshold are grouped together)</span>
                )}
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
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Document Similarity
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {/* Session & Upload Section - Top Left */}
        <Grid item xs={12} md={8}>
          <Paper elevation={0} sx={{ p: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)', height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Session & Upload
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              {showNewSession ? (
                <Box>
                  <TextField
                    fullWidth
                    label="Session Name"
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    size="small"
                    sx={{ mb: 2 }}
                  />
                  
                  <Typography id="similarity-threshold-slider" gutterBottom>
                    Similarity Threshold: {similarityThreshold}
                  </Typography>
                  
                  <Slider
                    value={similarityThreshold}
                    onChange={(e, value) => setSimilarityThreshold(value)}
                    step={0.05}
                    min={0.5}
                    max={0.95}
                    valueLabelDisplay="auto"
                    aria-labelledby="similarity-threshold-slider"
                    sx={{ mb: 1 }}
                  />
                  
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                    Higher values require documents to be more similar to be grouped together.
                    Documents with similarity score &gt;= threshold are grouped in the same bucket.
                  </Typography>
                  
                  <Typography variant="body2" sx={{ mb: 1.5 }}>
                    <strong>Session Text Processing:</strong>
                  </Typography>
                  
                  <PromptModelSelector
                    customPrompt={newSessionCustomPrompt}
                    setCustomPrompt={setNewSessionCustomPrompt}
                    promptModel={newSessionPromptModel}
                    setPromptModel={setNewSessionPromptModel}
                    rows={4}
                  />
                  
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                    These settings will be applied to all documents uploaded to this session.
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
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Button 
                startIcon={<AddIcon />} 
                onClick={() => setShowNewSession(true)}
                disabled={showNewSession}
                size="small"
              >
                New Session
              </Button>
              
              <Button
                startIcon={<RefreshIcon />}
                onClick={fetchSessions}
                disabled={loading}
                size="small"
              >
                Refresh
              </Button>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            {/* Document Upload */}
            <Typography variant="subtitle1" gutterBottom>
              Upload Document
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ mb: 1.5 }}>
                <strong>Session Preprocessing Settings:</strong>
              </Typography>
              
              <PromptModelSelector
                customPrompt={customPrompt}
                setCustomPrompt={setCustomPrompt}
                promptModel={promptModel}
                setPromptModel={setPromptModel}
                rows={3}
              />
              
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                These settings will be saved to the current session and applied to all documents.
              </Typography>
              
              <input
                ref={fileInputRef}
                id="file-upload"
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              
              <Button
                variant="outlined"
                onClick={triggerFileInput}
                fullWidth
                startIcon={<UploadIcon />}
                sx={{ mb: 1 }}
              >
                Select File
              </Button>
              
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
        </Grid>
        
        {/* Session Info - Top Right */}
        <Grid item xs={12} md={4}>
          <Paper elevation={0} sx={{ p: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)', height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Session Info
            </Typography>
            
            {loading && !selectedSession ? (
              <LinearProgress />
            ) : !selectedSession ? (
              <Typography variant="body1" sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                Select or create a session to view details
              </Typography>
            ) : (
              <Box>
                <Typography variant="body1">
                  <strong>Name:</strong> {sessions.find(s => s.id === selectedSession)?.name}
                </Typography>
                <Typography variant="body1">
                  <strong>Similarity Threshold:</strong> {sessions.find(s => s.id === selectedSession)?.similarity_threshold.toFixed(2)}
                </Typography>
                {sessions.find(s => s.id === selectedSession)?.custom_prompt && (
                  <>
                    <Typography variant="body1" sx={{ mb: 0.5 }}>
                      <strong>Custom Prompt:</strong>
                    </Typography>
                    <Box 
                      sx={{ 
                        maxHeight: '100px', 
                        overflowY: 'auto', 
                        p: 1, 
                        bgcolor: 'grey.50', 
                        borderRadius: 1,
                        mb: 1,
                        fontSize: '0.875rem'
                      }}
                    >
                      {sessions.find(s => s.id === selectedSession)?.custom_prompt}
                    </Box>
                  </>
                )}
                {sessions.find(s => s.id === selectedSession)?.prompt_model && (
                  <Typography variant="body1">
                    <strong>Prompt Model:</strong> {sessions.find(s => s.id === selectedSession)?.prompt_model}
                  </Typography>
                )}
                <Typography variant="body1">
                  <strong>Document Count:</strong> {sessionDocuments.length}
                </Typography>
                <Typography variant="body1">
                  <strong>Folder Count:</strong> {Object.keys(documentsByFolder).length}
                </Typography>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Session Actions
                  </Typography>
                  <Button
                    variant="outlined"
                    color="primary"
                    size="small"
                    onClick={() => fetchSessionDocuments(selectedSession)}
                    sx={{ mr: 1, mb: 1 }}
                  >
                    Refresh Documents
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    sx={{ mb: 1 }}
                  >
                    Delete Session
                  </Button>
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* Logs Section - Bottom Left */}
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={{ p: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Logs
              </Typography>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={clearLogs}
                disabled={logs.length === 0}
              >
                Clear Logs
              </Button>
            </Box>
            
            <Box sx={{ flexGrow: 1, overflow: 'auto', maxHeight: '500px' }}>
              {logs.length === 0 ? (
                <Typography variant="body1" sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                  No logs to display. Upload a document to see similarity processing logs.
                </Typography>
              ) : (
                logs.map((log, index) => (
                  <Box 
                    key={log.id || index} 
                    sx={{ 
                      p: 1, 
                      mb: 1, 
                      borderRadius: 1, 
                      bgcolor: log.type === 'error' ? 'error.50' : 
                              log.type === 'processing' ? 'grey.100' : 
                              'background.paper',
                      border: '1px solid',
                      borderColor: log.type === 'error' ? 'error.200' : 
                                  log.type === 'comparison' ? 'primary.100' : 
                                  log.type === 'processing' ? 'grey.300' : 
                                  'grey.200'
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="subtitle2" color={log.type === 'error' ? 'error' : 'text.primary'}>
                        {log.title || log.type || 'Log Entry'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </Typography>
                    </Box>
                    {log.type === 'comparison' ? (
                      <Box>
                        <Typography variant="body2">
                          Comparing <strong>{log.details.documentA}</strong> with <strong>{log.details.documentB}</strong>
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                          <Chip 
                            size="small" 
                            label={`Score: ${(log.details.score * 100).toFixed(1)}%`} 
                            color={log.details.score >= 0.7 ? 'success' : 'default'}
                          />
                          <Chip size="small" label={`Method: ${log.details.method}`} />
                          <Chip size="small" label={log.details.decision} />
                        </Box>
                      </Box>
                    ) : (
                      <Typography variant="body2">
                        {log.message || log.details?.message || JSON.stringify(log.details)}
                      </Typography>
                    )}
                  </Box>
                ))
              )}
            </Box>
          </Paper>
        </Grid>
        
        {/* Documents Organized - Bottom Right */}
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={{ p: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Documents Organized
            </Typography>
            
            {loading && selectedSession ? (
              <LinearProgress />
            ) : !selectedSession ? (
              <Typography variant="body1" sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                Select a session to view documents
              </Typography>
            ) : sessionDocuments.length === 0 ? (
              <Typography variant="body1" sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                No documents in this session. Upload documents to organize them by similarity.
              </Typography>
            ) : (
              <Box sx={{ flexGrow: 1, overflow: 'auto', maxHeight: '500px' }}>
                {Object.entries(documentsByFolder).map(([folder, docs]) => (
                  <Box key={folder} sx={{ mb: 3 }}>
                    <Typography 
                      variant="subtitle1" 
                      sx={{ 
                        p: 1, 
                        bgcolor: 'primary.main', 
                        color: 'white', 
                        borderRadius: '4px 4px 0 0'
                      }}
                    >
                      {formatFolderName(folder)} ({docs.length})
                    </Typography>
                    
                    <List sx={{ 
                      p: 0, 
                      border: '1px solid', 
                      borderColor: 'primary.light',
                      borderTop: 'none',
                      borderRadius: '0 0 4px 4px',
                      bgcolor: 'background.paper'
                    }}>
                      {docs.map((doc) => {
                        // Extract just the filename without the UUID prefix
                        let displayName = doc.filename;
                        
                        // Check if the filename starts with a UUID pattern
                        // UUIDs typically have a pattern like: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                        // or a shortened version without dashes
                        const uuidPattern = /^[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}/i;
                        const shortUuidPattern = /^[a-f0-9]{8,32}/i;
                        
                        if (uuidPattern.test(displayName)) {
                          // If the filename contains a full UUID at the start, remove it
                          const uuidMatch = displayName.match(uuidPattern)[0];
                          // Check if there's a separator after the UUID (underscore, dash, etc.)
                          const separatorIndex = uuidMatch.length;
                          if (displayName.length > separatorIndex && /[-_]/.test(displayName[separatorIndex])) {
                            displayName = displayName.substring(separatorIndex + 1);
                          }
                        } else if (displayName.includes('_')) {
                          // Common case - filename has format "id_actualfilename.ext"
                          const firstUnderscoreIndex = displayName.indexOf('_');
                          const firstPart = displayName.substring(0, firstUnderscoreIndex);
                          
                          // If the first part looks like a hex ID (all hex chars), remove it
                          if (/^[a-f0-9]+$/i.test(firstPart)) {
                            displayName = displayName.substring(firstUnderscoreIndex + 1);
                          }
                        }
                        
                        return (
                          <ListItem 
                            key={doc.id} 
                            divider 
                            sx={{ 
                              py: 0.5,
                              '&:last-child': {
                                borderBottom: 'none'
                              }
                            }}
                          >
                            <ListItemIcon sx={{ minWidth: 40 }}>
                              <DocumentIcon color="primary" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={displayName} 
                              secondary={`ID: ${doc.id.substring(0, 8)}`} 
                              primaryTypographyProps={{ variant: 'body2' }}
                              secondaryTypographyProps={{ variant: 'caption' }}
                            />
                          </ListItem>
                        );
                      })}
                    </List>
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
