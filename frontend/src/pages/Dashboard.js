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
          and ask questions about their content. All documents are stored in a single master bucket with organized folders.
        </Typography>
      </Paper>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Documents
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Upload PDF, TXT, or MD files to process with RAG.
              </Typography>
              <Button
                variant="contained"
                component={RouterLink}
                to="/upload"
                startIcon={<UploadIcon />}
              >
                Upload
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                View Documents
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                You have {documentCount} document(s) uploaded.
              </Typography>
              <Button
                variant="contained"
                component={RouterLink}
                to="/documents"
                startIcon={<DocumentIcon />}
              >
                View All
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Ask Questions
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Ask questions about your documents using RAG.
              </Typography>
              <Button
                variant="contained"
                component={RouterLink}
                to="/ask"
                startIcon={<QuestionIcon />}
              >
                Ask
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard; 