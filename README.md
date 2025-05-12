# Skill Extraction & Resume Clustering Platform

A full-stack AI-powered platform for extracting skills from resumes (CVs), searching and clustering candidates, and managing top talent selection. Built with FastAPI (Python) for the backend and React (MUI) for the frontend.

## Features

- **Automated Skill Extraction**: Parses PDF resumes to extract skills and summaries using NLP.
- **Search Engine**: Search CVs by keyword using BFS, DFS, or hill-climbing algorithms.
- **Clustering**: Cluster candidates by skills using KMeans, Agglomerative, or DBSCAN algorithms.
- **Interactive Frontend**: Modern React UI for searching, clustering, and managing candidates.
- **Downloadable CVs**: Download original PDF resumes directly from the UI.
- **Customizable Clustering**: Tune clustering parameters and select top candidates per cluster.

## Project Structure

```
Skill Extraction Through Resume/
├── backend/           # FastAPI backend (APIs for search, clustering, PDF serving)
│   └── main.py
├── cv-search-app/     # React frontend (UI for search & cluster)
│   └── src/
├── data/              # Input PDF resumes (not tracked by git)
├── results/           # Output: search & clustering results (not tracked by git)
├── parse_pdfs.py      # Script to extract skills from PDFs
├── kmeans.py          # Skill clustering logic (KMeans, Agglomerative, DBSCAN)
├── searches.py        # Search algorithms (BFS, DFS, hill-climbing)
├── .gitignore         # Excludes data, results, venv, etc.
└── README.md          # Project documentation
```

## Backend (FastAPI)

- **APIs** for:
  - Listing all CVs and downloading PDFs
  - Searching CVs by keyword and algorithm
  - Running clustering on search results
  - Viewing cluster assignments and summaries
  - Selecting top candidates per cluster
- **Run locally:**
  ```bash
  cd "Skill Extraction Through Resume/backend"
  pip install -r requirements.txt  # (create this as needed)
  uvicorn main:app --reload
  ```
- **Depends on:** FastAPI, scikit-learn, numpy, pydantic, etc.

## Frontend (React + MUI)

- **Modern UI** for search, clustering, and candidate management
- **Run locally:**
  ```bash
  cd "Skill Extraction Through Resume/cv-search-app"
  npm install
  npm start
  ```
- **Features:**
  - Search resumes by keyword and algorithm
  - Download PDFs
  - Run and tune clustering
  - Select top candidates per cluster

## Skill Extraction Pipeline

- **parse_pdfs.py**: Extracts skills and summaries from all PDFs in `data/` and writes to `results.json`.
- **kmeans.py**: Clusters profiles by skills using various algorithms and outputs cluster analysis.
- **searches.py**: Implements BFS, DFS, and hill-climbing search over extracted profiles.

## Data & Results

- **data/**: Place your PDF resumes here (not tracked by git)
- **results/**: Stores search and clustering results (not tracked by git)

## Quickstart

1. Place PDF resumes in `data/`.
2. Run `parse_pdfs.py` to extract skills:
   ```bash
   python parse_pdfs.py
   ```
3. Start backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
4. Start frontend:
   ```bash
   cd cv-search-app
   npm install
   npm start
   ```
5. Open [http://localhost:3000](http://localhost:3000) and start searching & clustering!

## License

MIT License. See [LICENSE](LICENSE) for details. 
