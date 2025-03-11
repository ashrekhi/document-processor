import React, { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
} from '@mui/material';
import { CloudUpload as UploadIcon, Description as DocumentIcon, QuestionAnswer as QuestionIcon } from '@mui/icons-material';
import { listDocuments } from '../services/api';

function Dashboard() {
  const [documentCount, setDocumentCount] = useState(0);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const documents = await listDocuments();
        setDocumentCount(documents.length);
      } catch (error) {
        console.error('Error fetching documents:', error);
      }
    };

    fetchDocuments();
  }, []);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Welcome to the Document Processor
        </Typography>
        <Typography variant="body1" paragraph>
          This application allows you to upload documents, process them using Retrieval-Augmented Generation (RAG),
          and ask questions about their content. Each document is stored in its own isolated S3 bucket for enhanced security.
        </Typography>
      </Paper>
      
      <Grid container spacing={3}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Documents
              </Typography>
              <Typography variant="h3" color="primary">
                {documentCount}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Total documents uploaded
              </Typography>
              <Button
                variant="outlined"
                startIcon={<DocumentIcon />}
                component={RouterLink}
                to="/documents"
                fullWidth
              >
                View Documents
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Upload new documents to process
              </Typography>
              <Button
                variant="contained"
                color="primary"
                startIcon={<UploadIcon />}
                component={RouterLink}
                to="/upload"
                fullWidth
              >
                Upload Document
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Ask Questions
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Ask questions about your documents
              </Typography>
              <Button
                variant="contained"
                color="secondary"
                startIcon={<QuestionIcon />}
                component={RouterLink}
                to="/ask"
                fullWidth
              >
                Ask Questions
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard; 