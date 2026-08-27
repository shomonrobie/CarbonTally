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
  FormControl,
  Grid,
  Card,
  CardContent,
  Divider,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Close as CloseIcon,
  FilePresent as FilePresentIcon,
  Save as SaveIcon,
  Dashboard as DashboardIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  BarChart as BarChartIcon,
  GetApp as DownloadIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

// ============ ANIMATIONS ============
const float = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-6px); }
`;

const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
`;

const shimmer = keyframes`
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
`;

// ============ STYLED COMPONENTS ============
const UploadCard = styled(Paper)(({ theme, active, isDragging }) => ({
  padding: theme.spacing(4, 3),
  textAlign: 'center',
  cursor: 'pointer',
  borderRadius: '12px',
  backgroundColor: active ? '#fafdfa' : isDragging ? '#fafdfa' : '#ffffff',
  border: `1px solid ${active ? '#d1e7d1' : isDragging ? '#d1e7d1' : '#e8edf2'}`,
  transition: 'all 0.3s ease',
  position: 'relative',
  overflow: 'hidden',
  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
  '&:hover': {
    borderColor: active ? '#b8d4b8' : '#c8d0d8',
    boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
  },
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(2.5, 1.5),
  },
}));

const UploadIcon = styled(Box)(({ active }) => ({
  fontSize: '3rem',
  marginBottom: '0.75rem',
  display: 'inline-block',
  animation: active ? `${float} 3s ease-in-out infinite` : 'none',
  '@media (max-width: 640px)': {
    fontSize: '2.25rem',
    marginBottom: '0.5rem',
  },
}));

const TypeButton = styled(Button)(({ active }) => ({
  borderRadius: '8px',
  border: `1px solid ${active ? '#d1e7d1' : '#e8edf2'}`,
  backgroundColor: active ? '#f5faf5' : '#ffffff',
  color: active ? '#2d6a4f' : '#4a5a6a',
  fontWeight: active ? 500 : 400,
  fontSize: '0.82rem',
  padding: '0.5rem 1rem',
  minWidth: '80px',
  flex: 1,
  textTransform: 'none',
  transition: 'all 0.2s ease',
  '&:hover': {
    borderColor: active ? '#b8d4b8' : '#c8d0d8',
    backgroundColor: active ? '#f0f7f0' : '#f5f7f9',
  },
  '@media (max-width: 640px)': {
    fontSize: '0.7rem',
    padding: '0.35rem 0.5rem',
    minWidth: '55px',
  },
}));

const ShimmerProgress = styled(LinearProgress)({
  height: 3,
  borderRadius: 2,
  '& .MuiLinearProgress-bar': {
    background: 'linear-gradient(90deg, #b8d4b8, #6b9e6b, #b8d4b8)',
    backgroundSize: '200% auto',
    animation: `${shimmer} 2s ease-in-out infinite`,
  },
});

const StatusAlert = styled(Alert)(({ theme }) => ({
  marginTop: theme.spacing(1),
  animation: `${fadeIn} 0.3s ease forwards`,
  borderRadius: '8px',
  fontSize: '0.85rem',
  '& .MuiAlert-message': {
    fontSize: '0.85rem',
    [theme.breakpoints.down('sm')]: {
      fontSize: '0.78rem',
    },
  },
  '&.MuiAlert-standardSuccess': {
    backgroundColor: '#f0f7f0',
    color: '#2d6a4f',
  },
  '&.MuiAlert-standardInfo': {
    backgroundColor: '#f0f4f8',
    color: '#3a5a7a',
  },
}));

const ReviewTableContainer = styled(TableContainer)(({ theme }) => ({
  marginTop: theme.spacing(2),
  borderRadius: '8px',
  border: '1px solid #e8edf2',
  maxHeight: 400,
  overflow: 'auto',
  animation: `${fadeIn} 0.5s ease forwards`,
  '& .MuiTableCell-root': {
    fontSize: '0.82rem',
    padding: '10px 12px',
    borderBottom: '1px solid #f0f3f6',
    [theme.breakpoints.down('sm')]: {
      fontSize: '0.72rem',
      padding: '6px 8px',
    },
  },
  '& .MuiTableHead-root .MuiTableCell-root': {
    backgroundColor: '#f8fafc',
    color: '#3a4a5a',
    fontWeight: 600,
    fontSize: '0.78rem',
    textTransform: 'uppercase',
    letterSpacing: '0.3px',
    borderBottom: '1px solid #e8edf2',
  },
}));

const StatusBadge = styled(Chip)(({ status }) => {
  const colors = {
    verified: { bg: '#e8f5e8', color: '#2d6a4f' },
    needs_review: { bg: '#fef5e8', color: '#a67c4a' },
    error: { bg: '#fde8e8', color: '#a64a4a' },
  };
  const color = colors[status] || colors.needs_review;
  return {
    backgroundColor: color.bg,
    color: color.color,
    fontWeight: 500,
    fontSize: '0.68rem',
    height: 22,
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
  padding: theme.spacing(0.75, 1.5),
  backgroundColor: '#f5f7f9',
  borderRadius: '8px',
  margin: '0 auto',
  maxWidth: '90%',
  animation: `${fadeIn} 0.3s ease forwards`,
  [theme.breakpoints.down('sm')]: {
    gap: theme.spacing(0.5),
    padding: theme.spacing(0.5, 1),
    flexWrap: 'wrap',
    maxWidth: '95%',
  },
}));

const StatCard = styled(Card)(({ theme }) => ({
  borderRadius: '12px',
  border: '1px solid #e8edf2',
  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
  transition: 'all 0.3s ease',
  height: '100%',
  '&:hover': {
    boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    transform: 'translateY(-2px)',
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
    site: '', 
    category: 'Petrol', 
    consumption: 0,
    kgCO2e: 192.67,
    status: 'Site and consumption missing'
  },
  { 
    date: '2026-01-17', 
    site: 'Manchester Depot', 
    category: '', 
    consumption: 180.0,
    kgCO2e: 457.2,
    status: 'Category missing'
  },
  { 
    date: '2026-01-18', 
    site: '', 
    category: 'Electricity', 
    consumption: 450.0,
    kgCO2e: 93.2,
    status: 'Site missing'
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
    category: 'Natural Gas', 
    consumption: 320.0,
    kgCO2e: 58.61,
    status: 'verified'
  },
];

const CATEGORY_OPTIONS = ['Diesel', 'Petrol', 'AdBlue', 'Electricity', 'Natural Gas'];
const SITE_OPTIONS = [
  'Birmingham Hub',
  'Manchester Depot',
  'Leeds Office',
  'London Warehouse',
  'Bristol Facility',
  'Glasgow Depot',
  'Cardiff Office',
  'Other'
];

// Colors for charts
const COLORS = ['#2d6a4f', '#40916c', '#52b788', '#74c69d', '#95d5b2', '#b7e4c7', '#d8f3dc'];

// ============ DASHBOARD COMPONENT ============
function ExecutiveDashboard({ data, onClose, onUploadAnother }) {
  const [tabValue, setTabValue] = useState(0);

  // Filter only verified data for dashboard
  const verifiedData = data.filter(row => row.status === 'verified');
  
  // Calculate summary statistics
  const totalEmissions = verifiedData.reduce((sum, row) => sum + row.kgCO2e, 0);
  const totalConsumption = verifiedData.reduce((sum, row) => sum + (typeof row.consumption === 'number' ? row.consumption : parseFloat(row.consumption) || 0), 0);
  const totalRecords = verifiedData.length;

  // Group by category for pie chart
  const categoryData = verifiedData.reduce((acc, row) => {
    const key = row.category || 'Unknown';
    if (!acc[key]) acc[key] = 0;
    acc[key] += row.kgCO2e;
    return acc;
  }, {});

  const pieData = Object.keys(categoryData).map(key => ({
    name: key,
    value: Math.round(categoryData[key] * 100) / 100,
  }));

  // Group by date for trend chart
  const trendData = verifiedData.reduce((acc, row) => {
    const date = row.date || 'Unknown';
    if (!acc[date]) {
      acc[date] = { date, emissions: 0, consumption: 0, count: 0 };
    }
    acc[date].emissions += row.kgCO2e;
    acc[date].consumption += typeof row.consumption === 'number' ? row.consumption : parseFloat(row.consumption) || 0;
    acc[date].count += 1;
    return acc;
  }, {});

  const chartData = Object.values(trendData)
    .sort((a, b) => a.date.localeCompare(b.date))
    .map(d => ({
      ...d,
      emissions: Math.round(d.emissions * 100) / 100,
      consumption: Math.round(d.consumption * 100) / 100,
    }));

  // Group by site for bar chart
  const siteData = verifiedData.reduce((acc, row) => {
    const site = row.site || 'Unknown';
    if (!acc[site]) acc[site] = 0;
    acc[site] += row.kgCO2e;
    return acc;
  }, {});

  const siteChartData = Object.keys(siteData).map(key => ({
    name: key,
    emissions: Math.round(siteData[key] * 100) / 100,
  }));

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const formatNumber = (num) => {
    if (num >= 1000) {
      return (num / 1000).toFixed(2) + ' t';
    }
    return num.toFixed(2) + ' kg';
  };

  return (
    <Box sx={{ p: { xs: 1, sm: 2 }, maxWidth: 1200, mx: 'auto' }}>
      {/* Dashboard Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 600, color: '#1a2a3a' }}>
            📊 Executive Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Based on {totalRecords} verified records
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            size="small"
            sx={{ borderRadius: '8px', textTransform: 'none' }}
          >
            Export Report
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            size="small"
            sx={{ borderRadius: '8px', textTransform: 'none', bgcolor: '#3d6a4f' }}
            onClick={onUploadAnother}
          >
            Upload Another
          </Button>
        </Stack>
      </Box>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard>
            <CardContent>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                Total Emissions
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#2d6a4f' }}>
                {formatNumber(totalEmissions)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                CO₂ equivalent
              </Typography>
            </CardContent>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard>
            <CardContent>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                Total Consumption
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a5a7a' }}>
                {Math.round(totalConsumption).toLocaleString()} kWh/L
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Energy consumed
              </Typography>
            </CardContent>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard>
            <CardContent>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                Records
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#4a6a5a' }}>
                {totalRecords}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Verified entries
              </Typography>
            </CardContent>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard>
            <CardContent>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                Avg Intensity
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#a67c4a' }}>
                {totalRecords > 0 ? (totalEmissions / totalRecords).toFixed(2) : 0} kg
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Per record
              </Typography>
            </CardContent>
          </StatCard>
        </Grid>
      </Grid>

      {/* Tabs for different views */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ '& .MuiTab-root': { textTransform: 'none', fontWeight: 500 } }}>
          <Tab label="📈 Emissions Trend" />
          <Tab label="🏭 By Category" />
          <Tab label="📍 By Site" />
          <Tab label="📋 Data Table" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <Box sx={{ display: tabValue === 0 ? 'block' : 'none' }}>
        <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #e8edf2' }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 500 }}>Emissions Trend</Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8edf2" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" label={{ value: 'kg CO₂e', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} />
              <YAxis yAxisId="right" orientation="right" label={{ value: 'Consumption (kWh/L)', angle: 90, position: 'insideRight', style: { fontSize: 12 } }} />
              <Tooltip formatter={(value) => value.toFixed(2)} />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="emissions" stroke="#2d6a4f" strokeWidth={3} dot={{ r: 4 }} name="Emissions (kg CO₂e)" />
              <Line yAxisId="right" type="monotone" dataKey="consumption" stroke="#40916c" strokeWidth={2} dot={{ r: 3 }} name="Consumption" />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      </Box>

      <Box sx={{ display: tabValue === 1 ? 'block' : 'none' }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #e8edf2', height: '100%' }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 500 }}>Emissions by Category</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${value.toFixed(2)} kg CO₂e`} />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #e8edf2', height: '100%' }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 500 }}>Category Breakdown</Typography>
              <Box sx={{ mt: 2 }}>
                {pieData.map((item, index) => (
                  <Box key={item.name} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1, borderBottom: '1px solid #f0f3f6' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: COLORS[index % COLORS.length] }} />
                      <Typography variant="body2">{item.name}</Typography>
                    </Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{item.value.toFixed(2)} kg</Typography>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      <Box sx={{ display: tabValue === 2 ? 'block' : 'none' }}>
        <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #e8edf2' }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 500 }}>Emissions by Site</Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={siteChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8edf2" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'kg CO₂e', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} />
              <Tooltip formatter={(value) => `${value.toFixed(2)} kg CO₂e`} />
              <Bar dataKey="emissions" fill="#2d6a4f" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Box>

      <Box sx={{ display: tabValue === 3 ? 'block' : 'none' }}>
        <Paper sx={{ borderRadius: '12px', border: '1px solid #e8edf2', overflow: 'hidden' }}>
          <TableContainer sx={{ maxHeight: 400 }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Site</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="right">Consumption</TableCell>
                  <TableCell align="right">kg CO₂e</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {verifiedData.map((row, index) => (
                  <TableRow key={index} hover>
                    <TableCell>{row.date}</TableCell>
                    <TableCell>{row.site}</TableCell>
                    <TableCell>{row.category}</TableCell>
                    <TableCell align="right">{typeof row.consumption === 'number' ? row.consumption.toFixed(2) : row.consumption}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 500 }}>{row.kgCO2e.toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip label="Verified" size="small" sx={{ bgcolor: '#e8f5e8', color: '#2d6a4f', fontSize: '0.65rem' }} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Box>

      {/* Action buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button
          variant="outlined"
          onClick={onClose}
          sx={{ borderRadius: '8px', textTransform: 'none' }}
        >
          Close Dashboard
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          sx={{ borderRadius: '8px', textTransform: 'none', bgcolor: '#3d6a4f' }}
          onClick={() => alert('Dashboard data saved successfully!')}
        >
          Save Report
        </Button>
      </Box>
    </Box>
  );
}

// ============ MAIN COMPONENT ============
export default function CarbonTallyDemo() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [file, setFile] = useState(null);
  const [uploadType, setUploadType] = useState('fuel');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [data, setData] = useState([]);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);
  const [savedData, setSavedData] = useState([]);

  // Auto-play demo
  useEffect(() => {
    startDemo();
  }, []);

  const startDemo = () => {
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

      setTimeout(() => {
        clearInterval(interval);
        setProgress(100);
        setLoading(false);
        setData(MOCK_CSV_DATA);
        setShowReview(true);
        setShowSuccess(true);
        setStatus({ 
          type: 'success', 
          message: '✅ Data extracted! 5 verified, 1 needs review.' 
        });

        setTimeout(() => {
          setShowSuccess(false);
        }, 4000);
      }, 4000);
    }, 2500);
  };

  const handleManualUpload = () => {
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
    setShowDashboard(false);
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
    startDemo();
  };

  const handleTypeChange = (type) => {
    setUploadType(type);
  };

  const handleInputChange = (index, field, value) => {
    const newData = [...data];
    
    if (field === 'consumption') {
      if (value === '' || value === '.' || /^\d*\.?\d*$/.test(value)) {
        newData[index][field] = value;
        const category = newData[index].category;
        const consumptionNum = parseFloat(value);
        if (category && !isNaN(consumptionNum) && consumptionNum > 0) {
          const factor = category === 'Diesel' ? 2.54 : 
                        category === 'Petrol' ? 2.16 : 
                        category === 'Electricity' ? 0.20712 :
                        category === 'Natural Gas' ? 0.18316 : 0;
          newData[index].kgCO2e = parseFloat((consumptionNum * factor).toFixed(2));
          newData[index].status = 'verified';
          newData[index].issue = '';
        } else if (category && consumptionNum === 0) {
          newData[index].kgCO2e = 0;
          newData[index].status = 'needs_review';
          newData[index].issue = 'Zero consumption';
        }
      }
    } else {
      newData[index][field] = value;
      if (field === 'category' && value) {
        const consumptionNum = parseFloat(newData[index].consumption);
        if (!isNaN(consumptionNum) && consumptionNum > 0) {
          const factor = value === 'Diesel' ? 2.54 : 
                        value === 'Petrol' ? 2.16 : 
                        value === 'Electricity' ? 0.20712 :
                        value === 'Natural Gas' ? 0.18316 : 0;
          newData[index].kgCO2e = parseFloat((consumptionNum * factor).toFixed(2));
          newData[index].status = 'verified';
          newData[index].issue = '';
        }
      }
    }
    
    setData(newData);
  };

  const handleSaveRecords = () => {
    const verified = data.filter(row => row.status === 'verified');
    if (verified.length === 0) {
      setStatus({ type: 'error', message: 'No verified records to save!' });
      return;
    }
    
    setSavedData(verified);
    setShowDashboard(true);
    setStatus({ type: 'success', message: `✅ ${verified.length} records saved! Viewing dashboard.` });
  };

  const shouldShowSiteDropdown = (row) => {
    return row.status === 'needs_review' && row.issue === 'Missing Site';
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

  // If dashboard is showing, render it
  if (showDashboard && savedData.length > 0) {
    return (
      <ExecutiveDashboard 
        data={savedData}
        onClose={() => setShowDashboard(false)}
        onUploadAnother={() => {
          setShowDashboard(false);
          setFile(null);
          setData([]);
          setShowReview(false);
          setSavedData([]);
          setStatus(null);
          setProgress(0);
          setTimeout(startDemo, 500);
        }}
      />
    );
  }

  return (
    <Box sx={{ width: '100%', maxWidth: 700, mx: 'auto', px: { xs: 0, sm: 2 } }}>
      <UploadCard
        active={!!file}
        isDragging={isDragging}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleManualUpload}
        elevation={0}
      >
        <Stack 
          direction="row" 
          spacing={1} 
          sx={{ mb: 2.5, flexWrap: 'wrap', justifyContent: 'center' }}
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

        <UploadIcon active={!!file}>
          {file ? '✅' : isDragging ? '📥' : '📄'}
        </UploadIcon>

        {file ? (
          <FileNameBox onClick={(e) => e.stopPropagation()}>
            <FilePresentIcon fontSize="small" sx={{ color: '#6a7a8a' }} />
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: 500, 
                color: '#2d3a4a',
                wordBreak: 'break-all',
                fontSize: { xs: '0.8rem', sm: '0.85rem' }
              }}
            >
              {file.name}
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                color: '#8a9aaa', 
                fontSize: { xs: '0.6rem', sm: '0.7rem' } 
              }}
            >
              ({file.size} KB)
            </Typography>
            <IconButton 
              size="small" 
              onClick={handleRemoveFile}
              sx={{ 
                color: '#9a7a7a',
                '&:hover': { color: '#c0392b' }
              }}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </FileNameBox>
        ) : (
          <Box>
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 500, 
                color: '#2d3a4a',
                fontSize: { xs: '1rem', sm: '1.1rem' },
                mb: 0.5
              }}
            >
              {isDragging ? 'Drop your file here' : 'Drag & drop your file here'}
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: '#6a7a8a', 
                mb: 1.5, 
                fontSize: { xs: '0.85rem', sm: '0.9rem' } 
              }}
            >
              or click to browse
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                color: '#8a9aaa',
                fontSize: { xs: '0.7rem', sm: '0.8rem' },
                display: 'block'
              }}
            >
              Supports CSV, XLSX, PDF, JPG, PNG
            </Typography>
          </Box>
        )}

        {loading && (
          <Box sx={{ mt: 2.5 }}>
            <ShimmerProgress 
              variant="determinate" 
              value={Math.min(progress, 100)} 
            />
          </Box>
        )}

        {status && !showSuccess && (
          <StatusAlert 
            severity={getStatusColor(status.type)} 
            variant="standard"
          >
            {status.message}
          </StatusAlert>
        )}

        {showSuccess && (
          <StatusAlert severity="success" variant="standard">
            ✅ Data extracted! {verifiedCount} verified, {needsReviewCount} need review.
          </StatusAlert>
        )}
      </UploadCard>

      <Button
        fullWidth
        variant="contained"
        disabled={loading}
        onClick={handleManualUpload}
        sx={{
          mt: 1.5,
          py: 1.25,
          fontSize: { xs: '0.85rem', sm: '0.9rem' },
          fontWeight: 500,
          backgroundColor: loading ? '#b8c4d0' : '#3d6a4f',
          borderRadius: '8px',
          textTransform: 'none',
          color: '#ffffff',
          boxShadow: 'none',
          '&:hover': {
            backgroundColor: loading ? '#b8c4d0' : '#2d5a3f',
            boxShadow: '0 2px 8px rgba(45, 90, 63, 0.15)',
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

      {showReview && data.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            mb: 1.5, 
            flexWrap: 'wrap', 
            gap: 1 
          }}>
            <Typography 
              variant="h6" 
              sx={{ 
                fontSize: { xs: '0.95rem', sm: '1.1rem' },
                fontWeight: 500,
                color: '#2d3a4a'
              }}
            >
              ⚠️ Data Review Required
            </Typography>
            <Stack direction="row" spacing={1}>
              <Chip 
                label={`${verifiedCount} Verified`} 
                size="small" 
                sx={{ 
                  bgcolor: '#e8f5e8', 
                  color: '#2d6a4f', 
                  fontWeight: 500,
                  fontSize: '0.7rem',
                }}
              />
              <Chip 
                label={`${needsReviewCount} Need Review`} 
                size="small" 
                sx={{ 
                  bgcolor: '#fef5e8', 
                  color: '#a67c4a', 
                  fontWeight: 500,
                  fontSize: '0.7rem',
                }}
              />
            </Stack>
          </Box>

          <ReviewTableContainer component={Paper}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Site</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Consumption</TableCell>
                  <TableCell>kgCO₂e</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.map((row, index) => (
                  <TableRow 
                    key={index}
                    sx={{ 
                      bgcolor: row.status === 'needs_review' ? '#fdfaf5' : 'inherit',
                      '&:hover': { bgcolor: '#f5f7f9' },
                      '&:last-child td': { borderBottom: 0 },
                    }}
                  >
                    <TableCell>{row.date}</TableCell>
                    <TableCell>
                      <FormControl size="small" sx={{ minWidth: isMobile ? 100 : 140 }}>
                        <Select
                          value={row.site || ''}
                          onChange={(e) => handleInputChange(index, 'site', e.target.value)}
                          displayEmpty
                          sx={{
                            '& .MuiSelect-select': { 
                              fontSize: isMobile ? '0.7rem' : '0.8rem',
                              padding: '6px 8px',
                            }
                          }}
                        >
                          <MenuItem value="" sx={{ fontSize: '0.8rem' }}>
                            <em>Select site...</em>
                          </MenuItem>
                          {SITE_OPTIONS.map((site) => (
                            <MenuItem key={site} value={site} sx={{ fontSize: '0.8rem' }}>
                              {site}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </TableCell>
                    <TableCell>
                      <Select
                        size="small"
                        value={row.category}
                        onChange={(e) => handleInputChange(index, 'category', e.target.value)}
                        sx={{ 
                          minWidth: isMobile ? 80 : 110,
                          '& .MuiSelect-select': { 
                            fontSize: isMobile ? '0.7rem' : '0.8rem',
                            padding: '6px 8px',
                          }
                        }}
                        displayEmpty
                      >
                        <MenuItem value="" sx={{ fontSize: '0.8rem' }}>Select...</MenuItem>
                        {CATEGORY_OPTIONS.map(opt => (
                          <MenuItem key={opt} value={opt} sx={{ fontSize: '0.8rem' }}>{opt}</MenuItem>
                        ))}
                      </Select>
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        type="text"
                        placeholder="0.00"
                        value={row.consumption}
                        onChange={(e) => handleInputChange(index, 'consumption', e.target.value)}
                        sx={{ 
                          width: isMobile ? 70 : 100,
                          '& .MuiInputBase-root': { 
                            fontSize: isMobile ? '0.7rem' : '0.8rem',
                            borderRadius: '6px',
                          },
                          '& input': {
                            textAlign: 'right',
                          }
                        }}
                        inputProps={{
                          inputMode: 'decimal',
                          pattern: '[0-9]*\\.?[0-9]*',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      {row.kgCO2e > 0 ? row.kgCO2e.toFixed(2) : '0'}
                    </TableCell>
                    <TableCell>
                      <StatusBadge 
                        label={row.status === 'verified' ? 'Verified' : 'Needs Review'} 
                        status={row.status}
                        size="small"
                      />
                      {row.issue && (
                        <Typography 
                          variant="caption" 
                          display="block" 
                          sx={{ 
                            color: '#a67c4a', 
                            fontSize: '0.6rem',
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

          <Button
            fullWidth
            variant="contained"
            size="large"
            startIcon={<DashboardIcon />}
            onClick={handleSaveRecords}
            sx={{
              mt: 2,
              py: 1.25,
              fontSize: { xs: '0.85rem', sm: '0.9rem' },
              fontWeight: 500,
              backgroundColor: '#3d6a4f',
              borderRadius: '8px',
              textTransform: 'none',
              color: '#ffffff',
              boxShadow: 'none',
              '&:hover': {
                backgroundColor: '#2d5a3f',
                boxShadow: '0 2px 8px rgba(45, 90, 63, 0.15)',
              },
            }}
          >
            📊 View Executive Dashboard ({verifiedCount} Verified Records)
          </Button>
        </Box>
      )}
    </Box>
  );
}