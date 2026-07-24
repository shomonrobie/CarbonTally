import React, { useState, useEffect } from 'react';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Select,
  MenuItem,
  TextField,
  useTheme,
  useMediaQuery,
  keyframes,
  styled,
} from '@mui/material';
import {
  Close as CloseIcon,
  FilePresent as FilePresentIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Save as SaveIcon,
} from '@mui/icons-material';

// ============ ANIMATIONS ============
const float = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
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
const UploadCard = styled(Paper)(({ theme, active, isDragging }) => ({
  padding: theme.spacing(4, 3),
  textAlign: 'center',
  cursor: 'pointer',
  border: `2px dashed ${active ? '#16a34a' : isDragging ? '#16a34a' : '#cbd5e1'}`,
  borderRadius: '12px',
  backgroundColor: active ? '#f0fdf4' : isDragging ? '#f0fdf4' : '#f8fafc',
  transition: 'all 0.3s ease',
  position: 'relative',
  overflow: 'hidden',
  '&:hover': {
    borderColor: active ? '#16a34a' : '#94a3b8',
    transform: 'translateY(-4px)',
    boxShadow: '0 8px 30px rgba(0,0,0,0.08)',
  },
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(2, 1.5),
  },
}));

const UploadIcon = styled(Box)(({ active }) => ({
  fontSize: '3.5rem',
  marginBottom: '1rem',
  display: 'inline-block',
  animation: active ? `${float} 3s ease-in-out infinite` : 'none',
  '@media (max-width: 640px)': {
    fontSize: '2.5rem',
    marginBottom: '0.75rem',
  },
}));

const TypeButton = styled(Button)(({ active }) => ({
  borderRadius: '8px',
  border: `2px solid ${active ? '#16a34a' : '#e2e8f0'}`,
  backgroundColor: active ? '#f0fdf4' : '#ffffff',
  color: active ? '#16a34a' : '#64748b',
  fontWeight: active ? 600 : 500,
  fontSize: '0.85rem',
  padding: '0.5rem 1rem',
  minWidth: '80px',
  flex: 1,
  textTransform: 'none',
  transition: 'all 0.2s ease',
  '&:hover': {
    borderColor: active ? '#16a34a' : '#94a3b8',
    backgroundColor: active ? '#f0fdf4' : '#f1f5f9',
    transform: 'translateY(-2px)',
  },
  '@media (max-width: 640px)': {
    fontSize: '0.75rem',
    padding: '0.4rem 0.6rem',
    minWidth: '60px',
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
  borderRadius: '8px',
  '& .MuiAlert-message': {
    fontSize: theme.typography.body2.fontSize,
    [theme.breakpoints.down('sm')]: {
      fontSize: '0.8rem',
    },
  },
}));

const ReviewTableContainer = styled(TableContainer)(({ theme }) => ({
  marginTop: theme.spacing(2),
  borderRadius: '8px',
  border: '1px solid #e2e8f0',
  maxHeight: 400,
  overflow: 'auto',
  animation: `${fadeIn} 0.5s ease forwards`,
  '& .MuiTableCell-root': {
    fontSize: '0.85rem',
    [theme.breakpoints.down('sm')]: {
      fontSize: '0.75rem',
      padding: '6px 8px',
    },
  },
}));

const StatusBadge = styled(Chip)(({ status }) => {
  const colors = {
    verified: { bg: '#dcfce7', color: '#16a34a' },
    needs_review: { bg: '#fef3c7', color: '#d97706' },
    error: { bg: '#fee2e2', color: '#dc2626' },
  };
  const color = colors[status] || colors.needs_review;
  return {
    backgroundColor: color.bg,
    color: color.color,
    fontWeight: 500,
    fontSize: '0.7rem',
    height: 24,
    '& .MuiChip-label': {
      padding: '0 8px',
    },
  };
});

const FileNameBox = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: theme.spacing(1),
  padding: theme.spacing(1),
  backgroundColor: '#f1f5f9',
  borderRadius: '8px',
  margin: '0 auto',
  maxWidth: '90%',
  animation: `${fadeIn} 0.3s ease forwards`,
  [theme.breakpoints.down('sm')]: {
    gap: theme.spacing(0.5),
    padding: theme.spacing(0.75),
    flexWrap: 'wrap',
  },
}));

// ============ MOCK DATA ============
const MOCK_CSV_DATA = [
  { 
    date: '2026-01-15', 
    site: 'Birmingham Hub', 
    category: 'Diesel', 
    consumption: 245.5,
    kgCO2e: 623.57,
    status: 'verified'
  },
  { 
    date: '2026-01-16', 
    site: 'Birmingham Hub', 
    category: 'Petrol', 
    consumption: 89.2,
    kgCO2e: 192.67,
    status: 'verified'
  },
  { 
    date: '2026-01-17', 
    site: 'Manchester Depot', 
    category: '', 
    consumption: 0,
    kgCO2e: 0,
    status: 'needs_review',
    issue: 'Unrecognized Category'
  },
  { 
    date: '2026-01-18', 
    site: '', 
    category: 'Diesel', 
    consumption: 0,
    kgCO2e: 0,
    status: 'needs_review',
    issue: 'Missing Site'
  },
  { 
    date: '2026-01-19', 
    site: 'Birmingham Hub', 
    category: 'AdBlue', 
    consumption: 12.0,
    kgCO2e: 0,
    status: 'needs_review',
    issue: 'Zero Emissions (AdBlue)'
  },
  { 
    date: '2026-01-20', 
    site: 'Leeds Office', 
    category: 'Unknown Fuel', 
    consumption: 150.0,
    kgCO2e: 0,
    status: 'needs_review',
    issue: 'Unrecognized Category'
  },
];

const CATEGORY_OPTIONS = ['Diesel', 'Petrol', 'AdBlue', 'Electricity', 'Natural Gas'];

// ============ MAIN COMPONENT ============
export default function CarbonTallyDemo() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // State
  const [file, setFile] = useState(null);
  const [uploadType, setUploadType] = useState('fuel');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [data, setData] = useState([]);
  const [showSuccess, setShowSuccess] = useState(false);

  // Auto-play demo
  useEffect(() => {
    startDemo();
  }, []);

  const startDemo = () => {
    // Step 1: Select a file
    setTimeout(() => {
      const mockFile = {
        name: 'mock_uk_fuel_card_messy.csv',
        size: 2.8,
        type: 'fuel',
        isMock: true
      };
      setFile(mockFile);
      setUploadType('fuel');
      setStatus({ 
        type: 'info', 
        message: `📎 File selected: ${mockFile.name}` 
      });
    }, 1500);

    // Step 2: Upload and process
    setTimeout(() => {
      setLoading(true);
      setProgress(0);
      setStatus({ type: 'info', message: '⏳ Processing document...' });

      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 95) {
            clearInterval(interval);
            return 95;
          }
          return prev + Math.random() * 15;
        });
      }, 300);

      // Step 3: Show results with review queue
      setTimeout(() => {
        clearInterval(interval);
        setProgress(100);
        setLoading(false);
        setData(MOCK_CSV_DATA);
        setShowReview(true);
        setShowSuccess(true);
        setStatus({ 
          type: 'success', 
          message: '✅ Data extracted! 2 verified, 4 need review.' 
        });

        // Auto reset after showing review
        setTimeout(() => {
          setShowSuccess(false);
        }, 4000);
      }, 4000);
    }, 2500);
  };

  const handleManualUpload = () => {
    // Just trigger the demo again or show a message
    if (!showReview && !loading) {
      startDemo();
    }
  };

  const handleRemoveFile = (e) => {
    e.stopPropagation();
    setFile(null);
    setStatus(null);
    setProgress(0);
    setShowReview(false);
    setData([]);
    setShowSuccess(false);
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
    // Just restart the demo
    startDemo();
  };

  const handleTypeChange = (type) => {
    setUploadType(type);
  };

  const handleInputChange = (index, field, value) => {
    const newData = [...data];
    newData[index][field] = value;
    if (field === 'category' && value) {
      newData[index].status = 'verified';
      newData[index].issue = '';
      const consumption = parseFloat(newData[index].consumption) || 0;
      const factor = value === 'Diesel' ? 2.54 : value === 'Petrol' ? 2.16 : 0;
      newData[index].kgCO2e = parseFloat((consumption * factor).toFixed(2));
    }
    setData(newData);
  };

  const getStatusColor = (type) => {
    switch (type) {
      case 'success': return 'success';
      case 'error': return 'error';
      case 'info': return 'info';
      default: return 'info';
    }
  };

  const verifiedCount = data.filter(row => row.status === 'verified').length;
  const needsReviewCount = data.filter(row => row.status === 'needs_review').length;

  return (
    <Box sx={{ width: '100%', maxWidth: 700, mx: 'auto', px: { xs: 0, sm: 2 } }}>
      {/* Upload Card */}
      <UploadCard
        active={!!file}
        isDragging={isDragging}
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
            { id: 'fuel', label: '⛽ Scope 1: Fuel' },
            { id: 'utility', label: '🔌 Scope 2: Utility' },
            { id: 'scope3', label: '🌱 Scope 3: Travel/Waste' },
          ].map((type) => (
            <TypeButton
              key={type.id}
              active={uploadType === type.id}
              onClick={() => handleTypeChange(type.id)}
            >
              {isMobile ? (
                type.id === 'fuel' ? '⛽ Fuel' :
                type.id === 'utility' ? '🔌 Utility' :
                '🌱 Travel/Waste'
              ) : (
                type.label
              )}
            </TypeButton>
          ))}
        </Stack>

        {/* Upload Icon */}
        <UploadIcon active={!!file}>
          {file ? '✅' : isDragging ? '📥' : '📄'}
        </UploadIcon>

        {/* Content Area */}
        {file ? (
          <FileNameBox onClick={(e) => e.stopPropagation()}>
            <FilePresentIcon fontSize="small" sx={{ color: '#64748b' }} />
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: 500, 
                color: '#0f172a',
                wordBreak: 'break-all',
                fontSize: { xs: '0.8rem', sm: '0.9rem' }
              }}
            >
              {file.name}
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                color: '#94a3b8', 
                fontSize: { xs: '0.65rem', sm: '0.75rem' } 
              }}
            >
              ({file.size} KB)
            </Typography>
            <IconButton 
              size="small" 
              onClick={handleRemoveFile}
              sx={{ color: '#ef4444' }}
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
                color: '#0f172a',
                fontSize: { xs: '1rem', sm: '1.25rem' }
              }}
            >
              {isDragging ? 'Drop your file here' : 'Drag & drop your file here'}
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: '#64748b', 
                mb: 1, 
                fontSize: { xs: '0.85rem', sm: '0.95rem' } 
              }}
            >
              or click to browse
            </Typography>
            <Chip 
              label="Supports CSV, XLSX, PDF, JPG, PNG" 
              size="small" 
              variant="outlined"
              sx={{ 
                color: '#94a3b8', 
                fontSize: { xs: '0.65rem', sm: '0.75rem' },
                borderColor: '#e2e8f0',
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
        {status && !showSuccess && (
          <StatusAlert 
            severity={getStatusColor(status.type)} 
            variant="filled"
          >
            {status.message}
          </StatusAlert>
        )}

        {/* Success Message */}
        {showSuccess && (
          <StatusAlert severity="success" variant="filled">
            ✅ Data extracted! 2 verified, 4 need review.
          </StatusAlert>
        )}
      </UploadCard>

      {/* Upload Button */}
      <Button
        fullWidth
        variant="contained"
        disabled={loading}
        onClick={handleManualUpload}
        sx={{
          mt: 1.5,
          py: 1.5,
          fontSize: { xs: '0.85rem', sm: '1rem' },
          fontWeight: 600,
          backgroundColor: loading ? '#94a3b8' : '#16a34a',
          borderRadius: '8px',
          textTransform: 'none',
          color: '#ffffff',
          '&:hover': {
            backgroundColor: loading ? '#94a3b8' : '#15803d',
            transform: loading ? 'none' : 'translateY(-2px)',
            boxShadow: loading ? 'none' : '0 4px 12px rgba(22, 163, 74, 0.3)',
          },
        }}
      >
        {loading ? (
          `Processing... ${Math.round(Math.min(progress, 100))}%`
        ) : (
          uploadType === 'fuel' ? 'Calculate Scope 1 Emissions' :
          uploadType === 'utility' ? 'Calculate Scope 2 Emissions' :
          'Calculate Scope 3 Emissions'
        )}
      </Button>

      {/* Review Queue */}
      {showReview && data.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            mb: 1, 
            flexWrap: 'wrap', 
            gap: 1 
          }}>
            <Typography 
              variant="h6" 
              sx={{ 
                fontSize: { xs: '1rem', sm: '1.25rem' },
                fontWeight: 600,
                color: '#0f172a'
              }}
            >
              ⚠️ Data Review Required
            </Typography>
            <Stack direction="row" spacing={1}>
              <Chip 
                label={`✅ ${verifiedCount} Verified`} 
                size="small" 
                sx={{ bgcolor: '#dcfce7', color: '#16a34a', fontWeight: 500 }}
              />
              <Chip 
                label={`⚠️ ${needsReviewCount} Need Review`} 
                size="small" 
                sx={{ bgcolor: '#fef3c7', color: '#d97706', fontWeight: 500 }}
              />
            </Stack>
          </Box>

          <ReviewTableContainer component={Paper}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow sx={{ bgcolor: '#f8fafc' }}>
                  <TableCell sx={{ fontWeight: 600, color: '#0f172a' }}>Date</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: '#0f172a' }}>Site</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: '#0f172a' }}>Category</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: '#0f172a' }}>Consumption</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: '#0f172a' }}>kgCO2e</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: '#0f172a' }}>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.map((row, index) => (
                  <TableRow 
                    key={index}
                    sx={{ 
                      bgcolor: row.status === 'needs_review' ? '#fffbeb' : 'inherit',
                      '&:hover': { bgcolor: '#f1f5f9' },
                      '&:last-child td': { borderBottom: 0 },
                    }}
                  >
                    <TableCell>{row.date}</TableCell>
                    <TableCell>
                      {row.status === 'needs_review' && row.issue === 'Missing Site' ? (
                        <TextField
                          size="small"
                          placeholder="Enter site name"
                          value={row.site}
                          onChange={(e) => handleInputChange(index, 'site', e.target.value)}
                          sx={{ 
                            width: isMobile ? 80 : 120,
                            '& .MuiInputBase-root': { fontSize: isMobile ? '0.75rem' : '0.85rem' }
                          }}
                        />
                      ) : (
                        row.site || 'N/A'
                      )}
                    </TableCell>
                    <TableCell>
                      {row.status === 'needs_review' ? (
                        <Select
                          size="small"
                          value={row.category}
                          onChange={(e) => handleInputChange(index, 'category', e.target.value)}
                          sx={{ 
                            minWidth: isMobile ? 80 : 120,
                            '& .MuiSelect-select': { fontSize: isMobile ? '0.75rem' : '0.85rem' }
                          }}
                          displayEmpty
                        >
                          <MenuItem value="">Select...</MenuItem>
                          {CATEGORY_OPTIONS.map(opt => (
                            <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                          ))}
                        </Select>
                      ) : (
                        row.category
                      )}
                    </TableCell>
                    <TableCell>
                      {row.status === 'needs_review' && row.consumption === 0 ? (
                        <TextField
                          size="small"
                          type="number"
                          placeholder="Enter value"
                          value={row.consumption}
                          onChange={(e) => handleInputChange(index, 'consumption', parseFloat(e.target.value) || 0)}
                          sx={{ 
                            width: isMobile ? 60 : 100,
                            '& .MuiInputBase-root': { fontSize: isMobile ? '0.75rem' : '0.85rem' }
                          }}
                        />
                      ) : (
                        row.consumption
                      )}
                    </TableCell>
                    <TableCell>
                      {row.kgCO2e > 0 ? row.kgCO2e.toFixed(2) : '0'}
                    </TableCell>
                    <TableCell>
                      <StatusBadge 
                        label={row.status === 'verified' ? '✅ Verified' : '⚠️ Needs Review'} 
                        status={row.status}
                        size="small"
                      />
                      {row.issue && (
                        <Typography 
                          variant="caption" 
                          display="block" 
                          sx={{ 
                            color: '#dc2626', 
                            fontSize: '0.65rem',
                            mt: 0.25
                          }}
                        >
                          {row.issue}
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ReviewTableContainer>

          {/* Save Button */}
          <Button
            fullWidth
            variant="contained"
            color="success"
            size="large"
            startIcon={<SaveIcon />}
            sx={{
              mt: 2,
              py: 1.5,
              fontSize: { xs: '0.85rem', sm: '1rem' },
              fontWeight: 600,
              backgroundColor: '#16a34a',
              borderRadius: '8px',
              textTransform: 'none',
              '&:hover': {
                backgroundColor: '#15803d',
                transform: 'translateY(-2px)',
                boxShadow: '0 4px 12px rgba(22, 163, 74, 0.3)',
              },
            }}
          >
            💾 Save {verifiedCount} Verified Records
          </Button>
        </Box>
      )}
    </Box>
  );
}