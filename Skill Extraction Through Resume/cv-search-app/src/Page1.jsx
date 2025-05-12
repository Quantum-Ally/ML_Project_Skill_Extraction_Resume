import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Box,
  Typography,
  TextField,
  Select,
  MenuItem,
  Button,
  Grid,
  Card,
  CardContent,
  Snackbar,
  Alert,
  InputLabel,
  FormControl
} from '@mui/material';

const API_BASE_URL = 'http://localhost:8000';

const algorithms = [
  { value: 'bfs', label: 'BFS' },
  { value: 'dfs', label: 'DFS' },
  { value: 'hill', label: 'Hill Climbing' },
];

export default function SearchDashboard() {
  const [keyword, setKeyword] = useState('');
  const [count, setCount] = useState(5);
  const [algo, setAlgo] = useState('bfs');
  const [results, setResults] = useState([]);
  const [totalStored, setTotalStored] = useState(0);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Load total on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/search/total`)
      .then(res => res.json())
      .then(n => setTotalStored(n))
      .catch(() => setTotalStored(0));
  }, []);

  const handleSearch = async () => {
    try {
      const q = new URLSearchParams({ algo, keyword, count });
      const res = await fetch(`${API_BASE_URL}/search?${q}`);
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      setResults(data);
      const total = await (await fetch(`${API_BASE_URL}/search/total`)).json();
      setTotalStored(total);
      setSnackbar({ open: true, message: 'Search completed!', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Network error during search', severity: 'error' });
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4, mb: 4, borderRadius: 4, background: 'linear-gradient(120deg, #e3e9f6 0%, #f4f6fa 100%)', boxShadow: 6 }}>
        <Typography variant="h4" gutterBottom align="center" sx={{ fontWeight: 700, color: 'primary.main', letterSpacing: 1 }}>AI CV Search</Typography>
        <Typography variant="subtitle1" color="text.secondary" align="center" gutterBottom sx={{ mb: 2 }}>
          Powered by FastAPI & React
        </Typography>
        <Box component="form" sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', mb: 2 }}>
          <TextField
            label="Keyword"
            placeholder="e.g. Python"
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            sx={{ minWidth: 180, background: '#fff', borderRadius: 1, boxShadow: 1 }}
          />
          <TextField
            label="Count"
            type="number"
            inputProps={{ min: 1 }}
            value={count}
            onChange={e => setCount(+e.target.value)}
            sx={{ minWidth: 120, background: '#fff', borderRadius: 1, boxShadow: 1 }}
          />
          <FormControl sx={{ minWidth: 180, background: '#fff', borderRadius: 1, boxShadow: 1 }}>
            <InputLabel id="algo-label">Algorithm</InputLabel>
            <Select
              labelId="algo-label"
              value={algo}
              label="Algorithm"
              onChange={e => setAlgo(e.target.value)}
            >
              {algorithms.map(opt => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSearch}
            sx={{ borderRadius: 2, fontWeight: 600, textTransform: 'none', px: 3 }}
          >
            Search
          </Button>
        </Box>
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 2 }}>
          Total Stored Results: {totalStored}
        </Typography>
      </Paper>
      <Grid container spacing={3}>
        {results.map(cv => (
          <Grid item xs={12} sm={6} md={4} key={cv.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', bgcolor: 'background.paper', boxShadow: 6, borderRadius: 4, transition: 'transform 0.2s, box-shadow 0.2s', '&:hover': { transform: 'translateY(-6px) scale(1.03)', boxShadow: 12 } }}>
              <CardContent>
                <Typography variant="h6" color="primary" gutterBottom sx={{ fontWeight: 600 }}>
                  {cv.id}
                </Typography>
                <Button
                  variant="outlined"
                  color="secondary"
                  href={`${API_BASE_URL}/cvs/${cv.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ borderRadius: 2, fontWeight: 600, textTransform: 'none', px: 2 }}
                >
                  Download PDF
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
