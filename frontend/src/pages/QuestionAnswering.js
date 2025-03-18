import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  FormControl,
  FormLabel,
  FormGroup,
  Divider,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Select,
  MenuItem,
  InputLabel,
} from '@mui/material';
import { Send as SendIcon, QuestionAnswer as QuestionIcon } from '@mui/icons-material';
import { askQuestion, getFolders } from '../services/api';

function QuestionAnswering() {
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [foldersLoading, setFoldersLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState('gpt-3.5-turbo');

  const models = [
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
    { id: 'gpt-4', name: 'GPT-4' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Ask Questions
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
        <Paper elevation={2} sx={{ p: 3, flex: 1 }}>
          <Typography variant="h6" gutterBottom>
            Ask Questions by Folder
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Select Folder
          </Typography>
          
          {foldersLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          ) : folders.length === 0 ? (
            <Alert severity="info">
              No folders found. Please create folders first.
            </Alert>
          ) : (
            <FormControl fullWidth>
              <InputLabel id="folder-select-label">Folder</InputLabel>
              <Select
                labelId="folder-select-label"
                id="folder-select"
                value={selectedFolder}
                label="Folder"
                onChange={handleFolderChange}
              >
                {folders.map((folder) => (
                  <MenuItem key={folder} value={folder}>
                    {folder}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          
          <Divider sx={{ my: 2 }} />
          
          <FormControl fullWidth margin="normal">
            <InputLabel id="model-select-label">Model</InputLabel>
            <Select
              labelId="model-select-label"
              id="model-select"
              value={selectedModel}
              label="Model"
              onChange={handleModelChange}
            >
              {models.map((model) => (
                <MenuItem key={model.id} value={model.id}>
                  {model.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <form onSubmit={handleSubmit}>
            <TextField
              label="Your Question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              fullWidth
              required
              margin="normal"
              multiline
              rows={3}
              placeholder="Ask a question about documents in the selected folder..."
            />
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={loading || foldersLoading || folders.length === 0}
                startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              >
                {loading ? 'Processing...' : 'Ask Question'}
              </Button>
            </Box>
          </form>
        </Paper>
        
        <Box sx={{ flex: 1 }}>
          <Typography variant="h6" gutterBottom>
            Answer
          </Typography>
          
          <Card variant="outlined" sx={{ height: '100%', minHeight: 300 }}>
            <CardContent>
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <CircularProgress />
                </Box>
              ) : answer ? (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <QuestionIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="subtitle1" fontWeight="bold">
                      {question}
                    </Typography>
                  </Box>
                  
                  <Divider sx={{ mb: 2 }} />
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Model: {models.find(m => m.id === selectedModel)?.name || selectedModel} • Folder: {selectedFolder}
                  </Typography>
                  
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                    {answer}
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'text.secondary' }}>
                  <Typography variant="body2">
                    Ask a question to see the answer here
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
}

export default QuestionAnswering; 