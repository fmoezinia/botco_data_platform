# Botco Data Platform

A data visualization and annotation platform for robotics data, featuring video playback, frame-by-frame navigation, and annotation tools.

## Features

- 🎥 Video playback with frame-by-frame navigation
- 📦 Bounding box annotations
- 📊 Graph visualizations with timers
- 📈 Data analytics dashboard
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
│   ├── init_mock_data.py
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

4. Initialize mock data:
   ```bash
   python init_mock_data.py
   ```

5. Start the backend server:
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

- `GET /videos` - Get list of all videos
- `GET /videos/{video_id}` - Get video metadata
- `GET /videos/{video_id}/frames/{frame_number}` - Get specific frame
- `GET /annotations/{video_id}` - Get annotations for a video
- `POST /annotations` - Create new annotation

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

## Development Status

✅ Project structure setup  
✅ React frontend with TypeScript  
✅ Tailwind CSS styling  
✅ Python backend with FastAPI  
✅ Dashboard layout  
✅ Video player component  
✅ Mock data setup  

🚧 In Progress:
- Annotation tools (bounding boxes, graphs)
- D3.js integration
- Real video frame extraction

📋 TODO:
- File upload functionality
- Real-time data streaming
- Export capabilities
- Advanced analytics
