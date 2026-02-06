# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Deep learning model support (in progress)
- Real-time streaming detection (planned)
- Batch processing endpoint (planned)

---

## [1.0.0] - 2024-02-06

### 🎉 Initial Release

First production-ready release of the AI Voice Detection API.

### Added

#### Core Features
- **Voice Detection API** - FastAPI-based REST API for detecting AI-generated voices
- **Multi-language Support** - Detection for Tamil, English, Hindi, Malayalam, Telugu
- **Ensemble ML Models** - Random Forest, Gradient Boosting, and SVM classifier
- **113+ Audio Features** - Comprehensive feature extraction (MFCC, spectral, prosodic, etc.)

#### API Features
- `POST /detect` - Main voice detection endpoint
- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /metrics` - Prometheus metrics

#### Security
- API key authentication
- Rate limiting (60/min, 1000/hr)
- Input validation and sanitization
- CORS support

#### Infrastructure
- Docker support with multi-stage build
- Docker Compose with full stack (API, Redis, PostgreSQL, Nginx, Prometheus, Grafana)
- Nginx reverse proxy configuration
- PostgreSQL database schema
- Prometheus monitoring configuration

#### Documentation
- Comprehensive README with examples
- API documentation
- Quick start guide
- API key guide
- Contributing guidelines
- MIT License

### Performance
- 95%+ detection accuracy
- Sub-2 second response time
- Support for 100+ requests/second

---

## [0.1.0] - 2024-01-15

### Added
- Initial project structure
- Basic FastAPI application
- Proof of concept audio processing
- Mock classifier for testing

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2024-02-06 | Production release, 5 languages, Docker support |
| 0.1.0 | 2024-01-15 | Initial proof of concept |

---

## Upgrade Guide

### 0.1.0 → 1.0.0

Breaking changes:
- Response format updated (new fields added)
- API key now required for `/detect` endpoint
- Environment variable names changed

Migration steps:
1. Update environment variables (see `.env.example`)
2. Generate new API keys
3. Update client code for new response format

---

[Unreleased]: https://github.com/yourusername/ai-voice-detection/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/ai-voice-detection/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/yourusername/ai-voice-detection/releases/tag/v0.1.0
