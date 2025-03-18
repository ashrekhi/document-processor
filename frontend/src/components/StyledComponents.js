import React from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Typography, 
  styled,
  Paper,
  Chip,
  TextField,
  Divider,
  CircularProgress,
  alpha
} from '@mui/material';

// Enhanced styled button with consistent styling
export const PrimaryButton = styled(Button)(({ theme }) => ({
  background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.primary.light} 90%)`,
  border: 0,
  borderRadius: 8,
  boxShadow: `0 3px 5px 2px ${alpha(theme.palette.primary.main, 0.3)}`,
  color: 'white',
  height: 48,
  padding: '0 30px',
  textTransform: 'none',
  fontWeight: 500,
  '&:hover': {
    boxShadow: `0 6px 10px 4px ${alpha(theme.palette.primary.main, 0.2)}`,
  }
}));

export const SecondaryButton = styled(Button)(({ theme }) => ({
  background: theme.palette.background.paper,
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: 8,
  color: theme.palette.text.primary,
  height: 48,
  padding: '0 30px',
  textTransform: 'none',
  fontWeight: 500,
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  }
}));

// Enhanced card with shadow and hover effect
export const EnhancedCard = styled(Card)(({ theme }) => ({
  borderRadius: 12,
  transition: 'all 0.3s ease-in-out',
  boxShadow: '0 4px 12px 0 rgba(0,0,0,0.05)',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0 12px 20px 0 rgba(0,0,0,0.1)',
  },
}));

// Section container with paper effect
export const SectionContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3),
  borderRadius: 12,
  boxShadow: '0 2px 12px 0 rgba(0,0,0,0.04)',
}));

// Styled text field with consistent appearance
export const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: 8,
    '& fieldset': {
      borderColor: theme.palette.divider,
    },
    '&:hover fieldset': {
      borderColor: theme.palette.primary.light,
    },
    '&.Mui-focused fieldset': {
      borderColor: theme.palette.primary.main,
    },
  },
}));

// Status chip for consistent status displays
export const StatusChip = ({ status, ...props }) => {
  const getStatusColor = (status) => {
    const statusMap = {
      active: 'success',
      pending: 'warning',
      inactive: 'error',
      completed: 'success',
      processing: 'info'
    };
    
    return statusMap[status.toLowerCase()] || 'default';
  };
  
  return (
    <Chip 
      color={getStatusColor(status)} 
      label={status} 
      size="small"
      {...props}
    />
  );
};

// Page header component
export const PageHeader = ({ title, subtitle, action }) => {
  return (
    <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <Box>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body1" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>
      {action && <Box>{action}</Box>}
    </Box>
  );
};

// Loading indicator component
export const LoadingIndicator = ({ size = 40, text = 'Loading...' }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', my: 4 }}>
      <CircularProgress size={size} />
      {text && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          {text}
        </Typography>
      )}
    </Box>
  );
};

// Empty state component
export const EmptyState = ({ title, description, icon, action }) => {
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        textAlign: 'center',
        py: 8,
      }}
    >
      {icon && (
        <Box sx={{ color: 'text.secondary', mb: 2, '& svg': { fontSize: 72 } }}>
          {icon}
        </Box>
      )}
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 400 }}>
        {description}
      </Typography>
      {action}
    </Box>
  );
};

// Panel divider with optional title
export const TitledDivider = ({ title }) => {
  return (
    <Box sx={{ width: '100%', my: 3, display: 'flex', alignItems: 'center' }}>
      {title ? (
        <>
          <Divider sx={{ flexGrow: 1 }} />
          <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
            {title}
          </Typography>
          <Divider sx={{ flexGrow: 1 }} />
        </>
      ) : (
        <Divider sx={{ flexGrow: 1 }} />
      )}
    </Box>
  );
}; 