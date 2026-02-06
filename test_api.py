"""
Test Client for AI Voice Detection API
Usage: python test_api.py --audio sample.mp3 --language english
"""

import argparse
import base64
import requests
import json
import time
from pathlib import Path
from typing import Dict, Any


class VoiceDetectionClient:
    """Client for testing the Voice Detection API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "demo_key_12345"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def detect_voice(self, audio_path: str, language: str) -> Dict[str, Any]:
        """
        Detect if audio is AI-generated or human
        
        Args:
            audio_path: Path to MP3 audio file
            language: Language of audio (tamil/english/hindi/malayalam/telugu)
        
        Returns:
            Detection result dictionary
        """
        # Read and encode audio
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Make request
        payload = {
            "audio_base64": audio_base64,
            "language": language
        }
        
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/detect",
            headers=self.headers,
            json=payload
        )
        elapsed_time = (time.time() - start_time) * 1000
        
        response.raise_for_status()
        result = response.json()
        result['client_elapsed_ms'] = round(elapsed_time, 2)
        
        return result
    
    def batch_detect(self, audio_files: list, language: str) -> list:
        """Detect multiple audio files"""
        results = []
        for audio_file in audio_files:
            try:
                result = self.detect_voice(audio_file, language)
                results.append({
                    'file': audio_file,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'file': audio_file,
                    'error': str(e)
                })
        return results


def print_result(result: Dict[str, Any], audio_path: str):
    """Pretty print detection result"""
    print("\n" + "="*60)
    print(f"🎙️  Audio File: {audio_path}")
    print("="*60)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    # Prediction with emoji
    prediction = result['prediction']
    emoji = "🤖" if prediction == "AI_GENERATED" else "👤"
    print(f"\n{emoji}  Prediction: {prediction}")
    
    # Confidence with bar
    confidence = result['confidence']
    bar_length = int(confidence * 40)
    bar = "█" * bar_length + "░" * (40 - bar_length)
    print(f"📊 Confidence: {confidence:.1%} [{bar}]")
    
    # Metadata
    print(f"\n📝 Details:")
    print(f"   Language: {result['language']}")
    print(f"   Audio Duration: {result['audio_duration_seconds']:.2f}s")
    print(f"   Processing Time: {result['processing_time_ms']:.2f}ms")
    print(f"   Client Elapsed: {result.get('client_elapsed_ms', 'N/A')}ms")
    print(f"   Timestamp: {result['timestamp']}")
    print(f"   Model Version: {result['model_version']}")
    
    # Interpretation
    print(f"\n💡 Interpretation:")
    if confidence >= 0.9:
        certainty = "very high"
    elif confidence >= 0.75:
        certainty = "high"
    elif confidence >= 0.6:
        certainty = "moderate"
    else:
        certainty = "low"
    
    print(f"   The model has {certainty} certainty that this audio is {prediction.lower().replace('_', ' ')}.")
    
    if prediction == "AI_GENERATED":
        print(f"   ⚠️  This voice appears to be synthesized by AI.")
    else:
        print(f"   ✅ This voice appears to be from a real human.")
    
    print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Test AI Voice Detection API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file detection
  python test_api.py --audio sample.mp3 --language english
  
  # Batch detection
  python test_api.py --batch audio1.mp3 audio2.mp3 --language tamil
  
  # Custom API endpoint
  python test_api.py --audio sample.mp3 --language hindi --url https://api.example.com
  
  # Custom API key
  python test_api.py --audio sample.mp3 --language malayalam --api-key your_key_here
        """
    )
    
    parser.add_argument(
        '--audio',
        type=str,
        help='Path to audio file (MP3)'
    )
    
    parser.add_argument(
        '--batch',
        nargs='+',
        help='Multiple audio files for batch processing'
    )
    
    parser.add_argument(
        '--language',
        type=str,
        required=True,
        choices=['tamil', 'english', 'hindi', 'malayalam', 'telugu'],
        help='Language of the audio'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8000',
        help='API base URL (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default='demo_key_12345',
        help='API key for authentication'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--health',
        action='store_true',
        help='Perform health check only'
    )
    
    args = parser.parse_args()
    
    # Initialize client
    client = VoiceDetectionClient(base_url=args.url, api_key=args.api_key)
    
    # Health check
    if args.health:
        try:
            health = client.health_check()
            print("\n✅ API is healthy!")
            print(json.dumps(health, indent=2))
        except Exception as e:
            print(f"\n❌ API health check failed: {e}")
        return
    
    # Validate input
    if not args.audio and not args.batch:
        parser.error("Either --audio or --batch is required")
    
    try:
        # Single file detection
        if args.audio:
            if not Path(args.audio).exists():
                print(f"❌ Error: File not found: {args.audio}")
                return
            
            result = client.detect_voice(args.audio, args.language)
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print_result(result, args.audio)
        
        # Batch detection
        elif args.batch:
            # Check all files exist
            for audio_file in args.batch:
                if not Path(audio_file).exists():
                    print(f"❌ Error: File not found: {audio_file}")
                    return
            
            print(f"\n🔄 Processing {len(args.batch)} files...")
            results = client.batch_detect(args.batch, args.language)
            
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                for item in results:
                    if 'error' in item:
                        print(f"\n❌ Error processing {item['file']}: {item['error']}")
                    else:
                        print_result(item['result'], item['file'])
                
                # Summary
                successful = sum(1 for r in results if 'error' not in r)
                ai_count = sum(1 for r in results if 'error' not in r and r['result']['prediction'] == 'AI_GENERATED')
                human_count = successful - ai_count
                
                print("\n" + "="*60)
                print("📊 Batch Summary")
                print("="*60)
                print(f"   Total files: {len(results)}")
                print(f"   Successful: {successful}")
                print(f"   🤖 AI Generated: {ai_count}")
                print(f"   👤 Human: {human_count}")
                print("="*60 + "\n")
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to API at {args.url}")
        print("   Make sure the API is running: uvicorn main:app --reload")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        if e.response.status_code == 403:
            print("   Check your API key")
        elif e.response.status_code == 422:
            print("   Check your input format")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
