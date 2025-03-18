import React, { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Grid,
  IconButton,
  LinearProgress,
  Stack,
  Typography,
  Paper,
} from '@mui/material';
import { 
  CloudUpload as UploadIcon, 
  Description as DocumentIcon, 
  QuestionAnswer as QuestionIcon, 
  MoreVert as MoreIcon,
  Folder as FolderIcon,
  TrendingUp as TrendingUpIcon,
  SwapVert as SwapVertIcon
} from '@mui/icons-material';
import { listDocuments } from '../services/api';

// Statistic box component
const StatCard = ({ icon, title, value, color, change }) => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h5" fontWeight="bold">
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {title}
            </Typography>
          </Box>
          <Avatar
            sx={{
              bgcolor: `${color}.light`,
              color: `${color}.main`,
              width: 48,
              height: 48,
            }}
          >
            {icon}
          </Avatar>
        </Box>
        {change && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
            <TrendingUpIcon color="success" fontSize="small" sx={{ mr: 0.5 }} />
            <Typography variant="caption" color="success.main" fontWeight="medium">
              {change}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

// Activity card component
const ActivityCard = ({ title, subtitle, icon, color }) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      <Avatar
        sx={{
          bgcolor: `${color}.light`,
          color: `${color}.main`,
          width: 40,
          height: 40,
          mr: 2,
        }}
      >
        {icon}
      </Avatar>
      <Box>
        <Typography variant="body2" fontWeight="medium">
          {title}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {subtitle}
        </Typography>
      </Box>
    </Box>
  );
};

function Dashboard() {
  const [documentCount, setDocumentCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setIsLoading(true);
        const documents = await listDocuments();
        setDocumentCount(documents.length);
      } catch (error) {
        console.error('Error fetching documents:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  // Simulated data for enterprise UI
  const documentTypes = [
    { type: 'PDF', count: Math.floor(documentCount * 0.6) || 0 },
    { type: 'TXT', count: Math.floor(documentCount * 0.3) || 0 },
    { type: 'MD', count: Math.floor(documentCount * 0.1) || 0 },
  ];
  
  const recentActivities = [
    { title: 'Document uploaded', subtitle: '3 minutes ago', icon: <UploadIcon />, color: 'primary' },
    { title: 'Question answered', subtitle: '10 minutes ago', icon: <QuestionIcon />, color: 'secondary' },
    { title: 'Folder created', subtitle: '1 hour ago', icon: <FolderIcon />, color: 'success' },
  ];

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Welcome to Document Processor
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your documents, organize with folders, and generate answers using RAG technology.
        </Typography>
      </Box>
      
      {isLoading && <LinearProgress sx={{ mb: 4 }} />}
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            icon={<DocumentIcon />} 
            title="Total Documents" 
            value={documentCount} 
            color="primary"
            change="12% increase" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            icon={<FolderIcon />} 
            title="Total Folders" 
            value="5" 
            color="secondary" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            icon={<QuestionIcon />} 
            title="Questions Asked" 
            value="24" 
            color="success"
            change="5% increase" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            icon={<SwapVertIcon />} 
            title="Processing Rate" 
            value="98%" 
            color="warning" 
          />
        </Grid>
      </Grid>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%' }}>
            <CardHeader 
              title="Quick Actions" 
              action={
                <IconButton>
                  <MoreIcon />
                </IconButton>
              }
            />
            <Divider />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={4}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      p: 2,
                      bgcolor: 'primary.light',
                      color: 'primary.contrastText',
                      position: 'relative',
                      overflow: 'hidden',
                    }}
                  >
                    <Box sx={{ position: 'absolute', right: -20, top: -20, opacity: 0.2 }}>
                      <UploadIcon sx={{ fontSize: 100 }} />
                    </Box>
                    <Box sx={{ position: 'relative', zIndex: 1 }}>
                      <Typography variant="h6" fontWeight="bold" gutterBottom>
                        Upload Documents
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                        Upload PDF, TXT, or MD files
                      </Typography>
                      <Button
                        variant="contained"
                        component={RouterLink}
                        to="/upload"
                        sx={{ 
                          bgcolor: 'white', 
                          color: 'primary.main',
                          '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' } 
                        }}
                      >
                        Upload Now
                      </Button>
                    </Box>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      p: 2,
                      bgcolor: 'secondary.light',
                      color: 'secondary.contrastText',
                      position: 'relative',
                      overflow: 'hidden',
                    }}
                  >
                    <Box sx={{ position: 'absolute', right: -20, top: -20, opacity: 0.2 }}>
                      <DocumentIcon sx={{ fontSize: 100 }} />
                    </Box>
                    <Box sx={{ position: 'relative', zIndex: 1 }}>
                      <Typography variant="h6" fontWeight="bold" gutterBottom>
                        View Documents
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                        Browse your documents
                      </Typography>
                      <Button
                        variant="contained"
                        component={RouterLink}
                        to="/documents"
                        sx={{ 
                          bgcolor: 'white', 
                          color: 'secondary.main',
                          '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' } 
                        }}
                      >
                        View All
                      </Button>
                    </Box>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      p: 2,
                      bgcolor: 'success.light',
                      color: 'success.contrastText',
                      position: 'relative',
                      overflow: 'hidden',
                    }}
                  >
                    <Box sx={{ position: 'absolute', right: -20, top: -20, opacity: 0.2 }}>
                      <QuestionIcon sx={{ fontSize: 100 }} />
                    </Box>
                    <Box sx={{ position: 'relative', zIndex: 1 }}>
                      <Typography variant="h6" fontWeight="bold" gutterBottom>
                        Ask Questions
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                        Get answers using RAG
                      </Typography>
                      <Button
                        variant="contained"
                        component={RouterLink}
                        to="/ask"
                        sx={{ 
                          bgcolor: 'white', 
                          color: 'success.main',
                          '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' } 
                        }}
                      >
                        Ask Now
                      </Button>
                    </Box>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardHeader 
              title="Document Overview" 
              action={
                <IconButton>
                  <MoreIcon />
                </IconButton>
              }
            />
            <Divider />
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Document Types
              </Typography>
              
              {documentTypes.map((docType) => (
                <Box key={docType.type} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">
                      {docType.type}
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {docType.count}
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={documentCount ? (docType.count / documentCount) * 100 : 0} 
                    sx={{ 
                      height: 6, 
                      borderRadius: 5,
                      bgcolor: 'background.default',
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 5,
                        bgcolor: docType.type === 'PDF' ? 'primary.main' : 
                                docType.type === 'TXT' ? 'secondary.main' : 'success.main',
                      }
                    }}
                  />
                </Box>
              ))}
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Recent Activity
              </Typography>
              
              {recentActivities.map((activity, index) => (
                <ActivityCard
                  key={index}
                  title={activity.title}
                  subtitle={activity.subtitle}
                  icon={activity.icon}
                  color={activity.color}
                />
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard; 