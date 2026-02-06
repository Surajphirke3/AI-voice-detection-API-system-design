"""
Pydantic Models for Request/Response Validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List
import base64


# Supported languages
SUPPORTED_LANGUAGES = ["tamil", "english", "hindi", "malayalam", "telugu"]


class VoiceDetectionRequest(BaseModel):
    """Request model for voice detection endpoint"""
    
    audio_base64: str = Field(
        ...,
        description="Base64-encoded audio file (MP3, WAV, or OGG)",
        min_length=100  # Minimum reasonable audio size
    )
    language: Literal["tamil", "english", "hindi", "malayalam", "telugu"] = Field(
        ...,
        description="Language of the audio sample"
    )
    
    @field_validator('audio_base64')
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """Validate base64 encoding"""
        try:
            decoded = base64.b64decode(v)
            if len(decoded) < 100:
                raise ValueError("Audio data too small")
            return v
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {str(e)}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_base64": "UklGRiQA...(base64 encoded audio)",
                "language": "english"
            }
        }


class VoiceDetectionResponse(BaseModel):
    """Response model for voice detection endpoint"""
    
    prediction: Literal["AI_GENERATED", "HUMAN"] = Field(
        ...,
        description="Classification result"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    language: str = Field(
        ...,
        description="Language of the analyzed audio"
    )
    processing_time_ms: float = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds"
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of the detection"
    )
    audio_duration_seconds: float = Field(
        ...,
        ge=0,
        description="Duration of the audio sample"
    )
    model_version: str = Field(
        default="1.0.0",
        description="Version of the detection model"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction": "AI_GENERATED",
                "confidence": 0.923,
                "language": "english",
                "processing_time_ms": 1234.56,
                "timestamp": "2024-02-05T10:30:00Z",
                "audio_duration_seconds": 5.2,
                "model_version": "1.0.0"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="Current health status"
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp"
    )
    version: str = Field(
        ...,
        description="API version"
    )
    model_loaded: bool = Field(
        default=True,
        description="Whether ML model is loaded"
    )


class ErrorResponse(BaseModel):
    """Standard error response"""
    
    detail: str = Field(
        ...,
        description="Error message"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code"
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp"
    )


class APIInfoResponse(BaseModel):
    """Response for root endpoint"""
    
    message: str
    version: str
    endpoints: dict
    supported_languages: List[str]
