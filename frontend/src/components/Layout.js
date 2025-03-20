import React from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  CloudUpload as UploadIcon,
  Description as DocumentIcon,
  QuestionAnswer as QuestionIcon,
  Folder as FolderIcon,
  DescriptionOutlined as LogoIcon,
  Brightness7 as LightModeIcon,
  Notifications as NotificationIcon,
  AccountCircle as ProfileIcon,
  Settings as SettingsIcon,
  Compare as CompareIcon,
  GroupWork as SessionIcon,
} from '@mui/icons-material';

const drawerWidth = 260;

function Layout({ children }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  // Restructured menu items with nested hierarchy
  const menuItems = [
    { 
      text: 'Dashboard', 
      icon: <DashboardIcon />, 
      path: '/',
      type: 'item'
    },
    { 
      text: 'Doc RAG Q&A', 
      icon: <QuestionIcon />, 
      type: 'category',
      items: [
        { text: 'Upload Documents', icon: <UploadIcon />, path: '/upload' },
        { text: 'Documents', icon: <DocumentIcon />, path: '/documents' },
        { text: 'Ask Questions', icon: <QuestionIcon />, path: '/ask' },
        { text: 'Folder Management', icon: <FolderIcon />, path: '/folders' },
      ] 
    },
    { 
      text: 'Document Similarity', 
      icon: <CompareIcon />, 
      type: 'category',
      items: [
        { text: 'Similarity Sessions', icon: <SessionIcon />, path: '/sessions' },
        { text: 'Check Similarity', icon: <CompareIcon />, path: '/similarity' },
      ] 
    },
  ];

  const drawer = (
    <div>
      <Box 
        sx={{
          display: 'flex',
          alignItems: 'center',
          py: 2.5,
          px: 2.5,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2 }}>
          <LogoIcon 
            sx={{ 
              color: theme.palette.primary.main,
              fontSize: 34,
              filter: 'drop-shadow(0px 1px 2px rgba(0,0,0,0.08))'
            }} 
          />
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 700,
              color: theme.palette.primary.main,
              letterSpacing: '0.5px',
              fontSize: '1.25rem'
            }}
          >
            DocProcessor
          </Typography>
        </Box>
      </Box>
      
      <Box sx={{ px: 2.5, py: 2.5 }}>
        <Typography 
          variant="caption" 
          sx={{ 
            color: theme.palette.text.secondary,
            fontWeight: 700,
            letterSpacing: '0.8px',
            fontSize: '0.75rem',
            display: 'block',
            px: 1,
            mb: 1.5,
            textTransform: 'uppercase'
          }}
        >
          MAIN MENU
        </Typography>
        
        <List sx={{ px: 0.5 }}>
          {menuItems.map((item, index) => {
            if (item.type === 'item') {
              const isActive = location.pathname === item.path;
              
              return (
                <ListItem key={item.text} disablePadding sx={{ mb: 0.75 }}>
                  <ListItemButton
                    component={RouterLink}
                    to={item.path}
                    selected={isActive}
                    onClick={isMobile ? handleDrawerToggle : undefined}
                    sx={{
                      borderRadius: 1.5,
                      py: 1.2,
                      px: 1.5,
                      transition: 'all 0.15s ease-in-out',
                      '&.Mui-selected': {
                        backgroundColor: theme.palette.primary.main + '14',
                        boxShadow: isActive ? '0 2px 8px rgba(0,0,0,0.05)' : 'none',
                        '&:hover': {
                          backgroundColor: theme.palette.primary.main + '20',
                        },
                        '& .MuiListItemIcon-root': {
                          color: theme.palette.primary.main,
                        },
                        '& .MuiTypography-root': {
                          fontWeight: 600,
                          color: theme.palette.primary.main,
                        }
                      },
                      '&:hover': {
                        backgroundColor: theme.palette.action.hover,
                      }
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        color: isActive ? theme.palette.primary.main : theme.palette.text.secondary,
                        minWidth: 36,
                        '& svg': {
                          fontSize: '1.25rem', 
                          transition: 'transform 0.2s',
                          transform: isActive ? 'scale(1.1)' : 'scale(1)',
                        }
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.text}
                      primaryTypographyProps={{
                        fontWeight: isActive ? 600 : 500,
                        fontSize: '0.875rem',
                        letterSpacing: '0.2px',
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              );
            } else if (item.type === 'category') {
              // Check if any child item is active
              const isAnyCategoryItemActive = item.items.some(
                subItem => location.pathname === subItem.path
              );
              
              return (
                <React.Fragment key={item.text}>
                  {/* Divider for categories except the first one */}
                  {index > 0 && (
                    <Divider sx={{ my: 2, mx: 1, opacity: 0.6 }} />
                  )}
                  
                  {/* Category Header */}
                  <Box sx={{ mt: index > 0 ? 1.5 : 0, mb: 1 }}>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        color: isAnyCategoryItemActive ? theme.palette.primary.main : theme.palette.text.secondary,
                        fontWeight: 600,
                        fontSize: '0.875rem',
                        letterSpacing: '0.3px',
                        display: 'flex',
                        alignItems: 'center',
                        px: 1.5,
                        py: 0.5,
                        transition: 'all 0.2s',
                        ...(isAnyCategoryItemActive && {
                          transform: 'translateX(2px)',
                        }),
                      }}
                    >
                      {item.icon && (
                        <Box component="span" sx={{ 
                          mr: 1.2, 
                          display: 'flex', 
                          alignItems: 'center',
                          transition: 'all 0.2s',
                          ...(isAnyCategoryItemActive && {
                            transform: 'scale(1.1)',
                          }),
                        }}>
                          {React.cloneElement(item.icon, { 
                            fontSize: 'small',
                            sx: { 
                              fontSize: '1.125rem',
                            }
                          })}
                        </Box>
                      )}
                      {item.text}
                    </Typography>
                  </Box>
                  
                  {/* Category Items */}
                  {item.items.map(subItem => {
                    const isActive = location.pathname === subItem.path;
                    
                    return (
                      <ListItem key={subItem.text} disablePadding sx={{ mb: 0.75 }}>
                        <ListItemButton
                          component={RouterLink}
                          to={subItem.path}
                          selected={isActive}
                          onClick={isMobile ? handleDrawerToggle : undefined}
                          sx={{
                            borderRadius: 1.5,
                            py: 0.9,
                            pl: 3.5,
                            pr: 1.5,
                            transition: 'all 0.15s ease-in-out',
                            '&.Mui-selected': {
                              backgroundColor: theme.palette.primary.main + '14',
                              boxShadow: isActive ? '0 2px 8px rgba(0,0,0,0.05)' : 'none',
                              '&:hover': {
                                backgroundColor: theme.palette.primary.main + '20',
                              },
                              '& .MuiListItemIcon-root': {
                                color: theme.palette.primary.main,
                              },
                              '& .MuiTypography-root': {
                                fontWeight: 600,
                                color: theme.palette.primary.main,
                              }
                            },
                            '&:hover': {
                              backgroundColor: theme.palette.action.hover,
                            }
                          }}
                        >
                          <ListItemIcon
                            sx={{
                              color: isActive ? theme.palette.primary.main : theme.palette.text.secondary,
                              minWidth: 32,
                              '& svg': {
                                fontSize: '1.125rem',
                                transition: 'transform 0.2s',
                                transform: isActive ? 'scale(1.1)' : 'scale(1)',
                              }
                            }}
                          >
                            {subItem.icon}
                          </ListItemIcon>
                          <ListItemText
                            primary={subItem.text}
                            primaryTypographyProps={{
                              fontWeight: isActive ? 600 : 500,
                              fontSize: '0.875rem',
                              letterSpacing: '0.2px',
                            }}
                          />
                        </ListItemButton>
                      </ListItem>
                    );
                  })}
                </React.Fragment>
              );
            }
            return null;
          })}
        </List>
      </Box>
      
      <Box sx={{ mt: 'auto', mb: 2, px: 3 }}>
        <Box
          sx={{
            p: 2.5,
            borderRadius: 2,
            bgcolor: theme.palette.primary.main + '14',
            color: theme.palette.primary.main,
          }}
        >
          <Typography variant="subtitle2" fontWeight={600} mb={1}>
            Need APIs?
          </Typography>
          <Typography variant="body2" mb={2}>
            Check our documentation for tips on how to use document processor APIs in your workflows.
          </Typography>
          <Button
            size="small"
            variant="contained"
            fullWidth
            href="https://docs.google.com/document/d/1yAtbJYuY8rN-bRHOhll_4227uosYOAPrbbbJhqHhDwk/edit?tab=t.0"
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              bgcolor: theme.palette.primary.main,
              '&:hover': {
                bgcolor: theme.palette.primary.dark,
              }
            }}
          >
            Documentation
          </Button>
        </Box>
      </Box>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        color="inherit"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          borderBottom: `1px solid ${theme.palette.divider}`,
          backgroundColor: 'background.paper',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" sx={{ flexGrow: 1, display: { xs: 'none', sm: 'block' } }}>
            {(() => {
              // Find active menu item and its parent category
              const currentPath = location.pathname;
              
              // Check if the current path is the dashboard
              if (currentPath === '/') {
                return 'Dashboard';
              }
              
              // Find which category contains the active item
              for (const category of menuItems) {
                if (category.type === 'category') {
                  const activeSubItem = category.items.find(item => item.path === currentPath);
                  if (activeSubItem) {
                    return `${category.text} / ${activeSubItem.text}`;
                  }
                }
              }
              
              // Fallback if no match found
              return 'Document Processor';
            })()}
          </Typography>
          
          <Stack direction="row" spacing={1} alignItems="center">
            <Tooltip title="Notifications">
              <IconButton color="default">
                <NotificationIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Settings">
              <IconButton color="default">
                <SettingsIcon />
              </IconButton>
            </Tooltip>
            
            <Divider orientation="vertical" flexItem sx={{ mx: 1, height: 24 }} />
            
            <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
              <Avatar
                sx={{
                  width: 36,
                  height: 36,
                  bgcolor: theme.palette.primary.main,
                }}
              >
                <ProfileIcon />
              </Avatar>
              <Box sx={{ ml: 1, display: { xs: 'none', sm: 'block' } }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, lineHeight: 1 }}>
                  Admin User
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Administrator
                </Typography>
              </Box>
            </Box>
          </Stack>
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={isMobile ? mobileOpen : true}
          onClose={isMobile ? handleDrawerToggle : undefined}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: `1px solid ${theme.palette.divider}`,
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          bgcolor: 'background.default',
          minHeight: '100vh',
        }}
      >
        <Toolbar />
        <Box sx={{ py: 2, px: { xs: 1, sm: 2 } }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}

export default Layout; 