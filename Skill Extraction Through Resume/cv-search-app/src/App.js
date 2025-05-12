import './App.css';
import { Routes, Route, Link as RouterLink } from 'react-router-dom';
import SearchDashboard from './Page1';
import ClusterManager from './Cluster';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';

function App() {
  return (
    <div className="App">
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            CV Search & Cluster
          </Typography>
          <Button color="inherit" component={RouterLink} to="/">Search</Button>
          <Button color="inherit" component={RouterLink} to="/cluster">Cluster</Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Routes>
          <Route path="/" element={<SearchDashboard />} />
          <Route path="/cluster" element={<ClusterManager />} />
        </Routes>
      </Container>
    </div>
  );
}

export default App;
