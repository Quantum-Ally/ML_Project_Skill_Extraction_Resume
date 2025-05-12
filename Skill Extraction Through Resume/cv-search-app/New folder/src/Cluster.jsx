// src/components/ClusterManager.jsx

import React, { useState, useEffect, useMemo } from 'react';
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
  FormControl,
  Slider,
  Chip,
  Stack
} from '@mui/material';

const API_BASE_URL = 'http://localhost:8000';

export default function ClusterManager() {
  // 1) Default params ↔ backend defaults
  const [algorithm, setAlgorithm] = useState('agglomerative');
  const [nClusters, setNClusters] = useState('');                 // None → auto
  const [minSkillFreq, setMinSkillFreq] = useState(2);
  const [dimReduction, setDimReduction] = useState('svd');
  const [dimComponents, setDimComponents] = useState(50);         // maps to dim_reduction_components
  const [dbscanEps, setDbscanEps] = useState(0.5);
  const [dbscanMinSamples, setDbscanMinSamples] = useState(5);

  // 2) Data
  const [summary, setSummary] = useState(null);
  const [assignmentsMap, setAssignmentsMap] = useState(null);
  const [selectCounts, setSelectCounts] = useState({});
  const [selectedGroups, setSelectedGroups] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // On mount, fetch both summary & raw assignments
  useEffect(() => {
    fetchSummary();
    fetchAssignments();
  }, []);

  async function fetchSummary() {
    try {
      const res = await fetch(`${API_BASE_URL}/cluster/summary`);
      const data = await res.json();
      setSummary(data);
      // initialize all pick-counts to zero
      const init = {};
      Object.keys(data.cluster_sizes).forEach(cid => (init[cid] = 0));
      setSelectCounts(init);
      setSelectedGroups(null);
    } catch (err) {
      setSummary(null);
    }
  }

  async function fetchAssignments() {
    try {
      const res = await fetch(`${API_BASE_URL}/cluster/results`);
      setAssignmentsMap(await res.json());
    } catch (err) {
      setAssignmentsMap(null);
    }
  }

  // group assignmentsMap → { clusterId: [id,...] }
  const grouped = useMemo(() => {
    if (!assignmentsMap) return {};
    return Object.entries(assignmentsMap).reduce((acc, [id, cid]) => {
      (acc[cid] = acc[cid] || []).push(id);
      return acc;
    }, {});
  }, [assignmentsMap]);

  // Run clustering with current form values
  async function handleRunClustering() {
    try {
      const params = new URLSearchParams({
        algorithm,
        ...(nClusters && { n_clusters: nClusters }),
        min_skill_freq: minSkillFreq,
        dim_reduction: dimReduction,
        dim_reduction_components: dimComponents,
        dbscan_eps: dbscanEps,
        dbscan_min_samples: dbscanMinSamples,
      });
      const res = await fetch(`${API_BASE_URL}/cluster/run?${params}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error(await res.text());
      await fetchSummary();
      await fetchAssignments();
      setSnackbar({ open: true, message: 'Clustering completed!', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Error running clustering', severity: 'error' });
    }
  }

  // Submit all pick counts at once
  async function handleSubmitSelection() {
    try {
      const res = await fetch(`${API_BASE_URL}/cluster/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ counts: selectCounts }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSelectedGroups(await res.json());
      setSnackbar({ open: true, message: 'Selection submitted!', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Error submitting selection', severity: 'error' });
    }
  }

  return (
    <Container maxWidth={false} sx={{ mt: 2, mb: 2, px: { xs: 1, sm: 2, md: 4 }, width: '100%', maxWidth: '1100px !important', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 3 }, mb: 3, borderRadius: 4, background: 'linear-gradient(120deg, #e3e9f6 0%, #f4f6fa 100%)', boxShadow: 6, width: '100%', maxWidth: 900 }}>
        <Typography variant="h4" gutterBottom align="center" sx={{ fontWeight: 700, color: 'primary.main', letterSpacing: 1 }}>Cluster Manager</Typography>
        <Typography variant="subtitle1" color="text.secondary" align="center" gutterBottom sx={{ mb: 2 }}>
          Run clustering & pick your top candidates
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', mb: 2 }}>
          <FormControl sx={{ minWidth: 180, background: '#fff', borderRadius: 1, boxShadow: 1 }}>
            <InputLabel id="algorithm-label">Algorithm</InputLabel>
            <Select
              labelId="algorithm-label"
              value={algorithm}
              label="Algorithm"
              onChange={e => setAlgorithm(e.target.value)}
            >
              <MenuItem value="kmeans">K-Means</MenuItem>
              <MenuItem value="agglomerative">Agglomerative</MenuItem>
              <MenuItem value="dbscan">DBSCAN</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="n_clusters"
            type="number"
            inputProps={{ min: 1 }}
            placeholder="auto"
            value={nClusters}
            onChange={e => setNClusters(e.target.value)}
            sx={{ minWidth: 120, background: '#fff', borderRadius: 1, boxShadow: 1 }}
          />
          <TextField
            label="min_skill_freq"
            type="number"
            inputProps={{ min: 1 }}
            value={minSkillFreq}
            onChange={e => setMinSkillFreq(+e.target.value)}
            sx={{ minWidth: 120, background: '#fff', borderRadius: 1, boxShadow: 1 }}
          />
          <FormControl sx={{ minWidth: 180, background: '#fff', borderRadius: 1, boxShadow: 1 }}>
            <InputLabel id="dim-reduction-label">Dim Reduction</InputLabel>
            <Select
              labelId="dim-reduction-label"
              value={dimReduction}
              label="Dim Reduction"
              onChange={e => setDimReduction(e.target.value)}
            >
              <MenuItem value="svd">SVD</MenuItem>
              <MenuItem value="None">None</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="dim_reduction_components"
            type="number"
            inputProps={{ min: 1 }}
            value={dimComponents}
            onChange={e => setDimComponents(+e.target.value)}
            sx={{ minWidth: 120, background: '#fff', borderRadius: 1, boxShadow: 1 }}
          />
          {algorithm === 'dbscan' && (
            <>
              <TextField
                label="dbscan_eps"
                type="number"
                inputProps={{ step: 0.1, min: 0 }}
                value={dbscanEps}
                onChange={e => setDbscanEps(+e.target.value)}
                sx={{ minWidth: 120, background: '#fff', borderRadius: 1, boxShadow: 1 }}
              />
              <TextField
                label="dbscan_min_samples"
                type="number"
                inputProps={{ min: 1 }}
                value={dbscanMinSamples}
                onChange={e => setDbscanMinSamples(+e.target.value)}
                sx={{ minWidth: 120, background: '#fff', borderRadius: 1, boxShadow: 1 }}
              />
            </>
          )}
          <Button
            variant="contained"
            color="primary"
            onClick={handleRunClustering}
            sx={{ borderRadius: 1, fontWeight: 600, textTransform: 'none', px: 3 }}
          >
            Run Clustering
          </Button>
        </Box>
      </Paper>
      {summary && (
        <Paper elevation={2} sx={{ p: 3, mb: 4, borderRadius: 4, background: '#fff', boxShadow: 4 }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 700, color: 'primary.main' }}>Cluster Summary</Typography>
          <Grid container spacing={3}>
            {Object.entries(summary.cluster_sizes).map(([cid, size]) => (
              <Grid item xs={12} sm={6} md={3} key={cid}>
                <Card sx={{ bgcolor: 'background.paper', boxShadow: 6, borderRadius: 4, transition: 'transform 0.2s, box-shadow 0.2s', '&:hover': { transform: 'translateY(-6px) scale(1.03)', boxShadow: 12 } }}>
                  <CardContent>
                    <Typography variant="subtitle1" color="primary" sx={{ fontWeight: 600 }}>Cluster {cid} ({size})</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Top: {summary.top_skills && summary.top_skills[cid] && summary.top_skills[cid].length > 0 ? (
                        <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                          {summary.top_skills[cid].map((skillObj, idx) => (
                            <Chip
                              key={idx}
                              label={typeof skillObj === 'object' && skillObj !== null ? skillObj.skill : String(skillObj)}
                              size="small"
                              sx={{ bgcolor: 'primary.light', color: 'primary.contrastText', fontWeight: 500, borderRadius: 1 }}
                            />
                          ))}
                        </Stack>
                      ) : '-'}
                    </Typography>
                    <TextField
                      label="Pick count"
                      type="number"
                      inputProps={{ min: 0, max: size }}
                      value={selectCounts[cid] || ''}
                      onChange={e => setSelectCounts({ ...selectCounts, [cid]: +e.target.value })}
                      size="small"
                      sx={{ width: 100, background: '#f4f6fa', borderRadius: 2 }}
                    />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          <Button
            variant="contained"
            color="secondary"
            onClick={handleSubmitSelection}
            sx={{ borderRadius: 2, fontWeight: 600, textTransform: 'none', px: 3, mt: 3 }}
          >
            Submit Selection
          </Button>
        </Paper>
      )}
      {selectedGroups && (
        <Paper elevation={2} sx={{ p: 2, mb: 3, borderRadius: 4, background: '#fff', boxShadow: 4, width: '100%', maxWidth: 900 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 700, color: 'primary.main' }}>Selected Candidates by Cluster</Typography>
          <Grid container spacing={3}>
            {Object.entries(selectedGroups).map(([cid, ids]) => (
              <Grid item xs={12} sm={6} md={3} key={cid}>
                <Card sx={{ bgcolor: 'background.paper', boxShadow: 6, borderRadius: 4, transition: 'transform 0.2s, box-shadow 0.2s', '&:hover': { transform: 'translateY(-6px) scale(1.03)', boxShadow: 12 } }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600 }}>Cluster {cid}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {ids.length > 0 ? (
                        <Stack direction="row" flexWrap="wrap" gap={1} mb={1}>
                          {ids.map(id => (
                            <Button
                              key={id}
                              variant="contained"
                              color="secondary"
                              href={`${API_BASE_URL}/cvs/${id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ borderRadius: 2, fontWeight: 600, textTransform: 'none', px: 2 }}
                            >
                              {id}
                            </Button>
                          ))}
                        </Stack>
                      ) : 'No candidates selected'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
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

