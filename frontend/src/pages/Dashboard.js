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
  SwapVert as SwapVertIcon,
  Compare as CompareIcon,
  GroupWork as SessionIcon
} from '@mui/icons-material';
import { listDocuments, listSessions } from '../services/api';

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

// Feature card component
const FeatureCard = ({ title, description, icon, color, buttonText, buttonLink }) => {
  return (
    <Card
      sx={{
        height: '100%',
        bgcolor: `${color}.light`,
        color: `${color}.contrastText`,
        borderRadius: 3,
        boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 20px rgba(0,0,0,0.15)',
        }
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar
            sx={{
              bgcolor: color + '.main',
              color: 'white',
              width: 56,
              height: 56,
              mr: 2,
              boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
            }}
          >
            {icon}
          </Avatar>
          <Typography variant="h5" fontWeight="bold">
            {title}
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ mb: 3, opacity: 0.9, minHeight: 80 }}>
          {description}
        </Typography>
        <Button
          variant="contained"
          component={RouterLink}
          to={buttonLink}
          size="large"
          startIcon={icon}
          sx={{ 
            bgcolor: color + '.main', 
            color: 'white',
            fontWeight: 'bold',
            '&:hover': { 
              bgcolor: color + '.dark',
              transform: 'scale(1.02)'
            },
            px: 3,
            py: 1,
            borderRadius: 2
          }}
        >
          {buttonText}
        </Button>
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
  const [sessionCount, setSessionCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [documents, sessions] = await Promise.all([
          listDocuments(),
          listSessions()
        ]);
        setDocumentCount(documents.length);
        setSessionCount(sessions.length);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Simulated data for UI
  const documentTypes = [
    { type: 'PDF', count: Math.floor(documentCount * 0.6) || 0 },
    { type: 'TXT', count: Math.floor(documentCount * 0.3) || 0 },
    { type: 'MD', count: Math.floor(documentCount * 0.1) || 0 },
  ];
  
  const recentActivities = [
    { title: 'Document uploaded', subtitle: '3 minutes ago', icon: <UploadIcon />, color: 'primary' },
    { title: 'Question answered', subtitle: '10 minutes ago', icon: <QuestionIcon />, color: 'success' },
    { title: 'Similarity checked', subtitle: '1 hour ago', icon: <CompareIcon />, color: 'secondary' },
  ];

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Document Processor
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Process your documents with powerful AI capabilities for RAG Q&A and similarity analysis.
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
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            icon={<FolderIcon />} 
            title="Document Folders" 
            value={(documentCount / 3).toFixed(0)} 
            color="success" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            icon={<SessionIcon />} 
            title="Similarity Sessions" 
            value={sessionCount} 
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            icon={<QuestionIcon />} 
            title="Questions Answered" 
            value="24" 
            color="warning" 
          />
        </Grid>
      </Grid>
      
      {/* Main Features Section */}
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>
        Main Features
      </Typography>
      
      <Grid container spacing={4} sx={{ mb: 5 }}>
        <Grid item xs={12} md={6}>
          <FeatureCard 
            title="Document RAG Q&A" 
            description="Upload documents, organize them into folders, and ask questions to get AI-powered answers using Retrieval Augmented Generation (RAG) technology."
            icon={<QuestionIcon />}
            color="success"
            buttonText="Use RAG Q&A"
            buttonLink="/documents"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <FeatureCard 
            title="Document Similarity" 
            description="Check document similarity to automatically organize uploads into buckets based on content similarity. Perfect for categorizing and managing similar documents."
            icon={<CompareIcon />}
            color="secondary"
            buttonText="Use Similarity"
            buttonLink="/sessions"
          />
        </Grid>
      </Grid>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%', borderRadius: 2, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
            <CardHeader 
              title="Quick Actions" 
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
                      borderRadius: 2,
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
                      bgcolor: 'success.light',
                      color: 'success.contrastText',
                      position: 'relative',
                      overflow: 'hidden',
                      borderRadius: 2,
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
                      borderRadius: 2,
                    }}
                  >
                    <Box sx={{ position: 'absolute', right: -20, top: -20, opacity: 0.2 }}>
                      <CompareIcon sx={{ fontSize: 100 }} />
                    </Box>
                    <Box sx={{ position: 'relative', zIndex: 1 }}>
                      <Typography variant="h6" fontWeight="bold" gutterBottom>
                        Check Similarity
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                        Organize by similarity
                      </Typography>
                      <Button
                        variant="contained"
                        component={RouterLink}
                        to="/similarity"
                        sx={{ 
                          bgcolor: 'white', 
                          color: 'secondary.main',
                          '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' } 
                        }}
                      >
                        Check Now
                      </Button>
                    </Box>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', borderRadius: 2, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
            <CardHeader 
              title="Activity Overview" 
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