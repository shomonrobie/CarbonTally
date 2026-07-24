import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Stack,
  LinearProgress,
  Alert,
  IconButton,
  useTheme,
  useMediaQuery,
  keyframes,
  styled,
} from '@mui/material';
import {
  Close as CloseIcon,
  FilePresent as FilePresentIcon,
} from '@mui/icons-material';

// ============ ANIMATIONS ============
const float = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-12px); }
`;

const shimmer = keyframes`
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
`;

const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

// ============ STYLED COMPONENTS ============
const UploadCard = styled(Paper)(({ theme, active }) => ({
  padding: theme.spacing(4, 3),
  textAlign: 'center',
  cursor: 'default',
  border: `2px dashed ${active ? theme.palette.success.main : theme.palette.grey[300]}`,
  borderRadius: theme.spacing(2),
  backgroundColor: active ? theme.palette.success.light : theme.palette.background.paper,
  transition: 'all 0.3s ease',
  position: 'relative',
  overflow: 'hidden',
  '&:hover': {
    borderColor: active ? theme.palette.success.main : theme.palette.grey[500],
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[8],
  },
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(2, 1.5),
  },
}));

const FloatingIcon = styled(Box)(({ active, theme }) => ({
  fontSize: '4rem',
  marginBottom: '1rem',
  display: 'inline-block',
  animation: active ? `${float} 3s ease-in-out infinite` : 'none',
  [theme.breakpoints.down('sm')]: {
    fontSize: '3rem',
    marginBottom: '0.75rem',
  },
}));

const TypeButton = styled(Button)(({ theme, active }) => ({
  borderRadius: theme.spacing(1),
  border: `2px solid ${active ? theme.palette.success.main : theme.palette.grey[300]}`,
  backgroundColor: active ? theme.palette.success.light : theme.palette.background.paper,
  color: active ? theme.palette.success.main : theme.palette.text.secondary,
  fontWeight: active ? 600 : 500,
  fontSize: '0.85rem',
  padding: theme.spacing(0.75, 2),
  minWidth: 80,
  flex: 1,
  textTransform: 'none',
  transition: 'all 0.2s ease',
  '&:hover': {
    borderColor: active ? theme.palette.success.main : theme.palette.grey[500],
    backgroundColor: active ? theme.palette.success.light : theme.palette.grey[50],
    transform: 'translateY(-2px)',
  },
  [theme.breakpoints.down('sm')]: {
    fontSize: '0.75rem',
    padding: theme.spacing(0.5, 1),
    minWidth: 60,
  },
}));

const ShimmerProgress = styled(LinearProgress)({
  height: 4,
  borderRadius: 4,
  '& .MuiLinearProgress-bar': {
    background: 'linear-gradient(90deg, #22c55e, #16a34a, #15803d)',
    backgroundSize: '200% auto',
    animation: `${shimmer} 2s ease-in-out infinite`,
  },
});

const StatusAlert = styled(Alert)(({ theme }) => ({
  marginTop: theme.spacing(1),
  animation: `${fadeIn} 0.3s ease forwards`,
  '& .MuiAlert-message': {
    fontSize: theme.typography.body2.fontSize,
    [theme.breakpoints.down('sm')]: {
      fontSize: '0.8rem',
    },
  },
}));

const FileNameBox = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: theme.spacing(1),
  padding: theme.spacing(1),
  backgroundColor: theme.palette.grey[100],
  borderRadius: theme.spacing(1),
  margin: '0 auto',
  maxWidth: '90%',
  animation: `${fadeIn} 0.3s ease forwards`,
  [theme.breakpoints.down('sm')]: {
    gap: theme.spacing(0.5),
    padding: theme.spacing(0.75),
  },
}));

const CTABanner = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(2),
  padding: theme.spacing(2),
  background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
  borderRadius: theme.spacing(1.5),
  textAlign: 'center',
  border: '1px solid #bbf7d0',
  animation: `${fadeIn} 0.6s ease forwards`,
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(1.5),
  },
}));

// ============ MOCK DATA ============
const MOCK_FILES = [
  { name: 'fuel-card-jan-2026.csv', size: 124.5, type: 'fuel' },
  { name: 'utility-bill-feb-2026.xlsx', size: 89.3, type: 'utility' },
  { name: 'travel-expenses-march-2026.csv', size: 45.7, type: 'scope3' },
  { name: 'electricity-invoice-q1-2026.pdf', size: 256.8, type: 'utility' },
  { name: 'vehicle-fleet-data-2026.csv', size: 312.4, type: 'fuel' },
];

// ============ MAIN COMPONENT ============
export default function FileUploadHero() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [file, setFile] = useState(null);
  const [uploadType, setUploadType] = useState('fuel');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Use useCallback to memoize startDemo
  const startDemo = useCallback(() => {
    // Step 1: Select a file after 1.5s
    const timeout1 = setTimeout(() => {
      const randomFile = MOCK_FILES[Math.floor(Math.random() * MOCK_FILES.length)];
      setFile({
        name: randomFile.name,
        size: randomFile.size,
        type: randomFile.type,
        isMock: true
      });
      setUploadType(randomFile.type);
      setStatus({ 
        type: 'info', 
        message: `📎 File selected: ${randomFile.name}` 
      });
    }, 1500);

    // Step 2: Upload after 2.5s
    const timeout2 = setTimeout(() => {
      setLoading(true);
      setProgress(0);
      setStatus({ type: 'info', message: '⏳ Processing document...' });

      // Simulate progress
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 95) {
            clearInterval(interval);
            return 95;
          }
          return prev + Math.random() * 15;
        });
      }, 300);

      // Step 3: Complete after 4s
      const timeout3 = setTimeout(() => {
        clearInterval(interval);
        setProgress(100);
        setLoading(false);
        setStatus({ 
          type: 'success', 
          message: '✅ Emissions calculated: 2,456 kg CO₂e' 
        });

        // Step 4: Reset after 3s and start over
        const timeout4 = setTimeout(() => {
          setStatus(null);
          setFile(null);
          setProgress(0);
          // Start the demo again
          startDemo();
        }, 3500);

        return () => clearTimeout(timeout4);
      }, 4000);

      return () => {
        clearInterval(interval);
        clearTimeout(timeout3);
      };
    }, 2500);

    return () => {
      clearTimeout(timeout1);
      clearTimeout(timeout2);
    };
  }, []);

  // Auto-play demo when component mounts
  useEffect(() => {
    const cleanup = startDemo();
    return cleanup;
  }, [startDemo]);

  const handleManualUpload = () => {
    // Show a CTA to sign up
    setStatus({ 
      type: 'info', 
      message: '🚀 Ready to process your real data? Sign up now!' 
    });
  };

  const handleRemoveFile = (e) => {
    e.stopPropagation();
    setFile(null);
    setStatus(null);
    setProgress(0);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    setStatus({ 
      type: 'info', 
      message: '💡 This is a demo. Sign up to upload your real files!' 
    });
  };

  const handleTypeChange = (type) => {
    setUploadType(type);
    if (file && file.isMock) {
      const mockFile = MOCK_FILES.find(f => f.type === type);
      if (mockFile) {
        setFile({
          name: mockFile.name,
          size: mockFile.size,
          type: mockFile.type,
          isMock: true
        });
      }
    }
  };

  const getStatusColor = (type) => {
    switch (type) {
      case 'success': return 'success';
      case 'error': return 'error';
      case 'info': return 'info';
      default: return 'info';
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 600, mx: 'auto', px: { xs: 1, sm: 2 } }}>
      <UploadCard
        active={!!file || isDragging}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleManualUpload}
        elevation={0}
      >
        {/* Type Selector */}
        <Stack 
          direction="row" 
          spacing={1} 
          sx={{ mb: 2, flexWrap: 'wrap', justifyContent: 'center' }}
          onClick={(e) => e.stopPropagation()}
        >
          {[
            { id: 'fuel', label: '⛽ Fuel' },
            { id: 'utility', label: '🔌 Utility' },
            { id: 'scope3', label: '🌱 Travel/Waste' },
          ].map((type) => (
            <TypeButton
              key={type.id}
              active={uploadType === type.id}
              onClick={() => handleTypeChange(type.id)}
              variant="outlined"
              size={isMobile ? 'small' : 'medium'}
            >
              {type.label}
            </TypeButton>
          ))}
        </Stack>

        {/* Upload Icon */}
        <FloatingIcon active={!!file}>
          {file ? '✅' : isDragging ? '📥' : '📄'}
        </FloatingIcon>

        {/* Content Area */}
        {file ? (
          <FileNameBox onClick={(e) => e.stopPropagation()}>
            <FilePresentIcon fontSize="small" />
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: 500, 
                color: 'text.primary',
                wordBreak: 'break-all',
                fontSize: { xs: '0.8rem', sm: '0.9rem' }
              }}
            >
              {file.name}
              {file.isMock && ' ✨'}
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                color: 'text.secondary', 
                fontSize: { xs: '0.65rem', sm: '0.75rem' } 
              }}
            >
              ({(file.size / 1024).toFixed(1)} KB)
            </Typography>
            <IconButton 
              size="small" 
              onClick={handleRemoveFile}
              sx={{ color: 'error.main' }}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </FileNameBox>
        ) : (
          <Box>
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 600, 
                color: 'text.primary',
                fontSize: { xs: '1rem', sm: '1.25rem' }
              }}
            >
              {isDragging ? 'Drop your file here' : 'Demo: Auto-upload in progress...'}
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: 'text.secondary', 
                mb: 1, 
                fontSize: { xs: '0.85rem', sm: '0.95rem' } 
              }}
            >
              Watch how easily CarbonTally processes your data
            </Typography>
            <Chip 
              label="Supports CSV, XLSX, PDF, JPG, PNG" 
              size="small" 
              variant="outlined"
              sx={{ 
                color: 'text.secondary', 
                fontSize: { xs: '0.65rem', sm: '0.75rem' } 
              }}
            />
          </Box>
        )}

        {/* Progress Bar */}
        {loading && (
          <Box sx={{ mt: 2 }}>
            <ShimmerProgress 
              variant="determinate" 
              value={Math.min(progress, 100)} 
            />
          </Box>
        )}

        {/* Status Message */}
        {status && (
          <StatusAlert 
            severity={getStatusColor(status.type)} 
            variant="filled"
          >
            {status.message}
          </StatusAlert>
        )}
      </UploadCard>

      {/* Upload Button */}
      <Button
        fullWidth
        variant="contained"
        color="success"
        size="large"
        onClick={handleManualUpload}
        disabled={loading}
        sx={{
          mt: 1.5,
          py: 1.5,
          fontSize: { xs: '0.85rem', sm: '1rem' },
          background: loading ? 'grey.400' : 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
          '&:hover': {
            background: loading ? 'grey.400' : 'linear-gradient(135deg, #15803d 0%, #166534 100%)',
            transform: loading ? 'none' : 'translateY(-2px)',
            boxShadow: loading ? 'none' : 4,
          },
        }}
      >
        {loading ? (
          `Processing... ${Math.round(Math.min(progress, 100))}%`
        ) : (
          uploadType === 'fuel' ? '⛽ Calculate Scope 1 Emissions' :
          uploadType === 'utility' ? '🔌 Calculate Scope 2 Emissions' :
          '🌱 Calculate Scope 3 Emissions'
        )}
      </Button>

      {/* CTA Banner */}
      <CTABanner>
        <Typography 
          variant="subtitle1" 
          sx={{ 
            fontWeight: 600, 
            color: 'text.primary',
            fontSize: { xs: '0.95rem', sm: '1.1rem' }
          }}
        >
          🚀 Try it for real!
        </Typography>
        <Typography 
          variant="body2" 
          sx={{ 
            color: 'text.secondary', 
            mb: 1.5,
            fontSize: { xs: '0.8rem', sm: '0.9rem' }
          }}
        >
          This is a demo. Sign up to upload your actual data and get instant emissions calculations.
        </Typography>
        <Button 
          variant="contained" 
          color="success" 
          onClick={() => window.location.href = '/signup'}
          sx={{
            px: 4,
            py: 1,
            fontSize: { xs: '0.85rem', sm: '0.95rem' },
            background: 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #15803d 0%, #166534 100%)',
            },
          }}
        >
          Start Free Trial →
        </Button>
      </CTABanner>
    </Box>
  );
}