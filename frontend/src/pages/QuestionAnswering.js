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
  FormControlLabel,
  Checkbox,
  Divider,
  CircularProgress,
  Alert,
  Card,
  CardContent,
} from '@mui/material';
import { Send as SendIcon, QuestionAnswer as QuestionIcon } from '@mui/icons-material';
import { listDocuments, askQuestion } from '../services/api';

function QuestionAnswering() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [documentsLoading, setDocumentsLoading] = useState(true);

  useEffect(() => {
    const fetchDocuments = async () => {
      setDocumentsLoading(true);
      
      try {
        const data = await listDocuments();
        setDocuments(data);
      } catch (error) {
        console.error('Error fetching documents:', error);
        setError('Failed to load documents. Please try again later.');
      } finally {
        setDocumentsLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  const handleDocumentChange = (event) => {
    const docId = event.target.value;
    
    if (event.target.checked) {
      setSelectedDocuments([...selectedDocuments, docId]);
    } else {
      setSelectedDocuments(selectedDocuments.filter(id => id !== docId));
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!question) {
      setError('Please enter a question');
      return;
    }
    
    if (selectedDocuments.length === 0) {
      setError('Please select at least one document');
      return;
    }
    
    setLoading(true);
    setError('');
    setAnswer('');
    
    try {
      const response = await askQuestion(question, selectedDocuments);
      setAnswer(response.answer);
    } catch (error) {
      console.error('Error asking question:', error);
      setError(error.response?.data?.detail || 'Error processing question');
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
            Select Documents
          </Typography>
          
          {documentsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          ) : documents.length === 0 ? (
            <Alert severity="info">
              No documents found. Please upload documents first.
            </Alert>
          ) : (
            <FormControl component="fieldset" sx={{ width: '100%' }}>
              <FormLabel component="legend">Choose documents to query:</FormLabel>
              <FormGroup>
                {documents.map((doc) => (
                  <FormControlLabel
                    key={doc.id}
                    control={
                      <Checkbox
                        checked={selectedDocuments.includes(doc.id)}
                        onChange={handleDocumentChange}
                        value={doc.id}
                      />
                    }
                    label={`${doc.filename} (${doc.source})`}
                  />
                ))}
              </FormGroup>
            </FormControl>
          )}
          
          <Divider sx={{ my: 2 }} />
          
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
              placeholder="Ask a question about the selected documents..."
            />
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={loading || documentsLoading || documents.length === 0}
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