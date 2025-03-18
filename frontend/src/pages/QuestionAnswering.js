import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Divider,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  Grid,
  IconButton,
  Chip,
  Avatar,
  alpha,
  useTheme
} from '@mui/material';
import { 
  Send as SendIcon, 
  QuestionAnswer as QuestionIcon,
  Folder as FolderIcon,
  SmartToy as AIIcon,
  Info as InfoIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { askQuestion, getFolders } from '../services/api';
import { 
  PageHeader, 
  StyledTextField, 
  PrimaryButton, 
  SectionContainer,
  LoadingIndicator,
  TitledDivider
} from '../components/StyledComponents';

function QuestionAnswering() {
  const theme = useTheme();
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [foldersLoading, setFoldersLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState('gpt-3.5-turbo');

  const models = [
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Fast and efficient for most queries' },
    { id: 'gpt-4', name: 'GPT-4', description: 'More powerful for complex questions' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', description: 'Latest version with improved capabilities' },
  ];

  useEffect(() => {
    const fetchFolders = async () => {
      setFoldersLoading(true);
      
      try {
        const data = await getFolders();
        // Filter out system folders like 'metadata'
        const userFolders = (data.folders || []).filter(folder => 
          folder !== 'metadata' && folder !== 'documents'
        );
        setFolders(userFolders);
        
        // Set default folder if available
        if (userFolders.length > 0 && !selectedFolder) {
          setSelectedFolder(userFolders[0]);
        }
      } catch (error) {
        console.error('Error fetching folders:', error);
        setError('Failed to load folders. Please try again later.');
      } finally {
        setFoldersLoading(false);
      }
    };

    fetchFolders();
  }, []);

  const handleFolderChange = (event) => {
    setSelectedFolder(event.target.value);
  };

  const handleModelChange = (event) => {
    setSelectedModel(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!question) {
      setError('Please enter a question');
      return;
    }
    
    if (!selectedFolder) {
      setError('Please select a folder');
      return;
    }
    
    setLoading(true);
    setError('');
    setAnswer('');
    
    try {
      console.log('Starting question submission...');
      console.log('Selected folder:', selectedFolder);
      
      const response = await askQuestion(
        question,
        null,
        selectedFolder,
        selectedModel
      );
      
      if (response && response.answer) {
        console.log('Successfully received answer of length:', response.answer.length);
        setAnswer(response.answer);
      } else {
        console.error('Received empty or invalid response:', response);
        setError('Received an empty or invalid response from the server');
      }
    } catch (error) {
      console.error('Error asking question:', error);
      const errorMessage = error.message || 'Error processing question';
      console.error('Error details:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  // Mock history for enterprise UI feel
  const questionHistory = [
    "What are the key points in the financial report?",
    "Summarize the legal contract from last month",
    "Extract data from the annual report"
  ];

  return (
    <Box>
      <PageHeader 
        title="Ask Questions" 
        subtitle="Ask questions about your documents using advanced RAG technology"
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
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={5} lg={4}>
          <SectionContainer>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Query Configuration
            </Typography>
            
            <TitledDivider title="Select Knowledge Source" />
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Folder
              </Typography>
              
              {foldersLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : folders.length === 0 ? (
                <Alert severity="info" sx={{ borderRadius: 2 }}>
                  No folders found. Please create folders first.
                </Alert>
              ) : (
                <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                  <InputLabel id="folder-select-label">Select Folder</InputLabel>
                  <Select
                    labelId="folder-select-label"
                    id="folder-select"
                    value={selectedFolder}
                    label="Select Folder"
                    onChange={handleFolderChange}
                    sx={{ borderRadius: 2 }}
                    startAdornment={
                      <FolderIcon sx={{ ml: 1, mr: 1, color: 'primary.main' }} />
                    }
                  >
                    {folders.map((folder) => (
                      <MenuItem key={folder} value={folder}>
                        {folder}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
              
              <Paper 
                variant="outlined" 
                sx={{ 
                  p: 1.5, 
                  bgcolor: alpha(theme.palette.info.main, 0.05),
                  borderRadius: 2,
                  borderColor: alpha(theme.palette.info.main, 0.2),
                  display: 'flex',
                  alignItems: 'flex-start'
                }}
              >
                <InfoIcon 
                  sx={{ 
                    mr: 1, 
                    mt: 0.2,
                    color: 'info.main',
                    fontSize: 18 
                  }} 
                />
                <Typography variant="caption" color="text.secondary">
                  The folder contains the documents that will be used as context for answering your questions.
                </Typography>
              </Paper>
            </Box>
            
            <TitledDivider title="AI Model Selection" />
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Model
              </Typography>
              
              <FormControl fullWidth variant="outlined">
                <InputLabel id="model-select-label">Select Model</InputLabel>
                <Select
                  labelId="model-select-label"
                  id="model-select"
                  value={selectedModel}
                  label="Select Model"
                  onChange={handleModelChange}
                  sx={{ borderRadius: 2 }}
                  startAdornment={
                    <AIIcon sx={{ ml: 1, mr: 1, color: 'secondary.main' }} />
                  }
                >
                  {models.map((model) => (
                    <MenuItem key={model.id} value={model.id}>
                      <Box>
                        <Typography variant="body2">
                          {model.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {model.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <TitledDivider title="Recent Questions" />
            
            <Box>
              {questionHistory.map((q, index) => (
                <Box 
                  key={index}
                  sx={{ 
                    display: 'flex',
                    alignItems: 'center',
                    mb: 1.5,
                    p: 1.5,
                    borderRadius: 2,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: 'action.hover'
                    }
                  }}
                  onClick={() => setQuestion(q)}
                >
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      mr: 1.5,
                      bgcolor: `${theme.palette.grey[200]}`,
                      color: `${theme.palette.text.secondary}`,
                    }}
                  >
                    <HistoryIcon fontSize="small" />
                  </Avatar>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {q}
                  </Typography>
                </Box>
              ))}
            </Box>
          </SectionContainer>
        </Grid>
        
        <Grid item xs={12} md={7} lg={8}>
          <SectionContainer sx={{ mb: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Ask Your Question
            </Typography>
            
            <form onSubmit={handleSubmit}>
              <StyledTextField
                label="Your Question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                fullWidth
                required
                margin="normal"
                multiline
                rows={3}
                placeholder="Ask a question about documents in the selected folder..."
                variant="outlined"
                sx={{ mb: 2 }}
              />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Chip 
                    icon={<FolderIcon fontSize="small" />} 
                    label={selectedFolder || 'No folder selected'} 
                    size="small"
                    color="primary"
                    sx={{ mr: 1 }}
                  />
                  <Chip 
                    icon={<AIIcon fontSize="small" />} 
                    label={models.find(m => m.id === selectedModel)?.name || selectedModel} 
                    size="small"
                    color="secondary"
                  />
                </Box>
                
                <PrimaryButton
                  type="submit"
                  disabled={loading || foldersLoading || folders.length === 0 || !question.trim()}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                >
                  {loading ? 'Processing...' : 'Ask Question'}
                </PrimaryButton>
              </Box>
            </form>
          </SectionContainer>
          
          <SectionContainer>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" fontWeight={600}>
                Answer
              </Typography>
              
              {answer && (
                <Chip 
                  label={`${models.find(m => m.id === selectedModel)?.name || selectedModel}`}
                  size="small" 
                  color="secondary"
                  variant="outlined"
                />
              )}
            </Box>
            
            <Box
              sx={{
                borderRadius: 2,
                bgcolor: 'background.default',
                p: 3,
                minHeight: 300,
              }}
            >
              {loading ? (
                <LoadingIndicator text="Generating answer..." />
              ) : answer ? (
                <Box>
                  <Box 
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'flex-start', 
                      mb: 2,
                      p: 2,
                      borderRadius: 2,
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                    }}
                  >
                    <QuestionIcon sx={{ mr: 1.5, color: 'primary.main', mt: 0.5 }} />
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                        Your Question:
                      </Typography>
                      <Typography variant="body2">
                        {question}
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Divider sx={{ mb: 3 }} />
                  
                  <Box sx={{ pl: 1 }}>
                    <Typography 
                      variant="body1" 
                      sx={{ 
                        whiteSpace: 'pre-line',
                        lineHeight: 1.7 
                      }}
                    >
                      {answer}
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column',
                  justifyContent: 'center', 
                  alignItems: 'center', 
                  height: '100%', 
                  minHeight: 300,
                  p: 3
                }}>
                  <QuestionIcon 
                    sx={{ 
                      fontSize: 60, 
                      color: alpha(theme.palette.text.secondary, 0.2),
                      mb: 2
                    }} 
                  />
                  <Typography variant="body2" color="text.secondary" align="center">
                    Ask a question about your documents to see the answer here
                  </Typography>
                </Box>
              )}
            </Box>
          </SectionContainer>
        </Grid>
      </Grid>
    </Box>
  );
}

export default QuestionAnswering; 