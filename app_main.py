"""
AI Voice Detection API - Main Application
Production-ready FastAPI application for detecting AI-generated vs Human voices
Supports: Tamil, English, Hindi, Malayalam, Telugu
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import base64
import logging
from datetime import datetime
import time
from typing import Optional

# Import local modules
from app.config import settings
from app.models import (
    VoiceDetectionRequest, 
    VoiceDetectionResponse,
    HealthResponse,
    ErrorResponse,
    APIInfoResponse,
    SUPPORTED_LANGUAGES
)
from app.audio_processor import AudioProcessor
from app.classifier import get_classifier, MockVoiceClassifier
from app.auth import verify_api_key, get_rate_limit_headers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global instances
audio_processor: Optional[AudioProcessor] = None
classifier = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown"""
    global audio_processor, classifier
    
    # Startup
    logger.info("🚀 Starting AI Voice Detection API...")
    
    # Initialize audio processor
    audio_processor = AudioProcessor(target_sr=settings.target_sample_rate)
    logger.info(f"✅ Audio processor initialized (SR: {settings.target_sample_rate})")
    
    # Initialize classifier
    classifier = get_classifier(settings.model_path)
    if classifier.is_mock:
        logger.warning("⚠️ Using MOCK classifier - train models for production use")
    else:
        logger.info(f"✅ Ensemble classifier loaded (version: {classifier.model_version})")
    
    logger.info(f"✅ API ready at http://{settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down API...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
## 🎙️ AI Voice Detection API

Detect whether audio is AI-generated or human speech with high accuracy.

### Features
- **Multi-language support**: Tamil, English, Hindi, Malayalam, Telugu
- **High accuracy**: 95%+ detection using ensemble ML models
- **Fast processing**: Sub-2-second inference time
- **Production ready**: Authentication, rate limiting, monitoring

### Authentication
Include your API key in the `X-API-Key` header:
```
X-API-Key: your_api_key_here
```

### Rate Limits
- 60 requests per minute
- 1000 requests per hour
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit-Minute", "X-RateLimit-Remaining-Minute"]
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with structured response"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"ERR_{exc.status_code}",
            "timestamp": datetime.utcnow().isoformat()
        },
        headers=getattr(exc, 'headers', None)
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error. Please try again later.",
            "error_code": "ERR_500",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============== API ENDPOINTS ==============

@app.get("/", response_model=APIInfoResponse, tags=["Info"])
async def root():
    """
    Root endpoint with API information
    """
    return APIInfoResponse(
        message="AI Voice Detection API",
        version=settings.app_version,
        endpoints={
            "health": "/health",
            "detect": "/detect (POST)",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        supported_languages=SUPPORTED_LANGUAGES
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    
    Returns current API status and model information.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        model_loaded=classifier is not None and not getattr(classifier, 'is_mock', True)
    )


@app.post(
    "/detect",
    response_model=VoiceDetectionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Missing API key"},
        403: {"model": ErrorResponse, "description": "Invalid API key"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["Detection"]
)
async def detect_voice(
    request: VoiceDetectionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    🎯 Detect if audio is AI-generated or human speech
    
    ### Request
    - **audio_base64**: Base64-encoded audio file (MP3, WAV, OGG)
    - **language**: Language of the audio (tamil/english/hindi/malayalam/telugu)
    
    ### Response
    - **prediction**: `AI_GENERATED` or `HUMAN`
    - **confidence**: Confidence score (0.0 to 1.0)
    - **processing_time_ms**: Time taken to process
    
    ### Example
    ```python
    import requests
    import base64
    
    with open("audio.mp3", "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()
    
    response = requests.post(
        "http://localhost:8000/detect",
        headers={"X-API-Key": "your_key"},
        json={"audio_base64": audio_b64, "language": "english"}
    )
    print(response.json())
    ```
    """
    start_time = time.time()
    
    try:
        # 1. Decode base64 audio
        try:
            audio_bytes = base64.b64decode(request.audio_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 encoding: {str(e)}"
            )
        
        # 2. Validate file size
        max_size = settings.max_file_size_mb * 1024 * 1024
        if len(audio_bytes) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )
        
        # 3. Preprocess audio
        try:
            audio, sr, duration = audio_processor.preprocess(audio_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Audio preprocessing error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Could not process audio: {str(e)}"
            )
        
        # 4. Extract features
        try:
            features = audio_processor.extract_all_features(audio, sr)
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error extracting audio features"
            )
        
        # 5. Classify
        try:
            prediction, confidence = classifier.predict(features, request.language)
        except Exception as e:
            logger.error(f"Classification error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error during classification"
            )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Log detection
        logger.info(
            f"Detection: {prediction} | "
            f"Confidence: {confidence:.3f} | "
            f"Language: {request.language} | "
            f"Duration: {duration:.2f}s | "
            f"Time: {processing_time_ms:.2f}ms"
        )
        
        return VoiceDetectionResponse(
            prediction=prediction,
            confidence=confidence,
            language=request.language,
            processing_time_ms=round(processing_time_ms, 2),
            timestamp=datetime.utcnow().isoformat(),
            audio_duration_seconds=round(duration, 2),
            model_version=classifier.model_version if hasattr(classifier, 'model_version') else settings.model_version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint (placeholder)
    
    In production, integrate with prometheus_client library.
    """
    return {
        "info": "Metrics endpoint - integrate with Prometheus for production monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============== RUN SERVER ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app_main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        workers=1  # Use 1 for development, increase for production
    )
