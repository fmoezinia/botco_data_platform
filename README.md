# Botco Data Platform

A professional robotics data visualization platform with AI-powered segmentation capabilities, featuring video playback, frame-by-frame navigation, and advanced annotation tools.

## Features

- 🎥 Video playback with frame-by-frame navigation
- 🤖 AI-powered SAM2 segmentation and visualization
- 📦 Bounding box annotations and object tracking
- 📊 Graph visualizations with timers
- 📈 Data analytics dashboard
- ☁️ Cloud storage support (AWS S3)
- 🔧 Python backend with FastAPI
- ⚛️ React frontend with TypeScript

## Project Structure

```
botco_data/
├── frontend/          # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   ├── types/
│   │   └── hooks/
│   └── package.json
├── backend/           # Python FastAPI backend
│   ├── main.py
│   ├── config.py
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── requirements.txt
└── README.md
```

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will be available at `http://localhost:3000`

## API Endpoints

### Core API
- `GET /api/v1/scenarios` - Get list of all scenarios
- `GET /api/v1/scenarios/{scenario_id}/scenes` - Get scenes for a scenario
- `GET /api/v1/scenarios/{scenario_id}/scenes/{scene_id}/episodes` - Get episodes for a scene
- `GET /api/v1/episodes/{episode_id}` - Get episode metadata and frames

### AI Processing
- `POST /api/v1/ai/process-video` - Process video with SAM2 segmentation
- `GET /api/v1/ai/tasks/{task_id}` - Get task status
- `POST /api/v1/ai/generate-visualization/{task_id}` - Generate visualization video

### Health & Monitoring
- `GET /health` - Health check endpoint

## Technology Stack

### Frontend
- React 18 with TypeScript
- Tailwind CSS for styling
- D3.js for data visualization

### Backend
- Python 3.8+
- FastAPI for REST API
- OpenCV for video processing
- Pydantic for data validation
- SAM2 for AI segmentation
- AWS S3 for cloud storage

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Application
DEBUG=false
APP_NAME="Botco Data Platform"
APP_VERSION="1.0.0"

# Server
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Data paths
DATA_DIR=data
VIDEOS_DIR=data/videos
VISUALIZATIONS_DIR=data/visualizations

# SAM2 AI
SAM2_MODEL_NAME=facebook/sam2-hiera-tiny
SAM2_DEVICE=auto

# AWS S3 (optional)
STORAGE_MODE=local  # or 's3'
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
```

## Development Status

✅ Professional project structure  
✅ React frontend with TypeScript  
✅ Tailwind CSS styling  
✅ Python backend with FastAPI  
✅ AI-powered SAM2 segmentation  
✅ Video visualization with overlays  
✅ Cloud storage support (AWS S3)  
✅ Proper error handling and logging  
✅ Configuration management  
✅ Health monitoring  

🚧 In Progress:
- Advanced annotation tools
- Real-time data streaming
- Export capabilities

📋 TODO:
- User authentication
- Advanced analytics dashboard
- Multi-user collaboration
