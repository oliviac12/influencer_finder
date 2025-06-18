"""
TikTok MCP Client - Interface for TikTok MCP subtitle extraction
"""
import json
import subprocess
import tempfile
import os

class TikTokMCPClient:
    def __init__(self, mcp_server_command=None):
        """
        Initialize TikTok MCP client
        
        Args:
            mcp_server_command: Command to run MCP server (if needed)
        """
        self.mcp_server_command = mcp_server_command or "npx -y @modelcontextprotocol/server-tiktok"
    
    def extract_subtitles(self, tiktok_url, format="text"):
        """
        Extract subtitles from TikTok video using MCP
        
        Args:
            tiktok_url: TikTok video URL
            format: Output format ('text', 'srt', 'vtt')
            
        Returns:
            dict: Result with success status and subtitle data
        """
        try:
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_video_transcript",
                    "arguments": {
                        "url": tiktok_url
                    }
                }
            }
            
            # Call MCP server
            result = self._call_mcp_server(mcp_request)
            
            if result.get('success'):
                return {
                    'success': True,
                    'subtitles': result.get('content', ''),
                    'language': result.get('language', 'unknown'),
                    'confidence': result.get('confidence', 0.0),
                    'url': tiktok_url
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown MCP error'),
                    'url': tiktok_url
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"MCP client error: {str(e)}",
                'url': tiktok_url
            }
    
    def _call_mcp_server(self, request):
        """
        Call the MCP server with the given request
        
        Args:
            request: MCP JSON-RPC request
            
        Returns:
            dict: Parsed response
        """
        try:
            # Convert request to JSON
            request_json = json.dumps(request)
            
            # Create temporary file for the request
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(request_json)
                temp_file = f.name
            
            try:
                # Call MCP server (adjust command based on your MCP setup)
                cmd = [
                    "mcp", "call", 
                    "--server", "tiktok",
                    "--method", "tools/call",
                    "--params", json.dumps(request["params"])
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Parse response
                    response = json.loads(result.stdout)
                    
                    if "result" in response:
                        # Extract content from MCP response
                        content = response["result"].get("content", [])
                        if content and len(content) > 0:
                            text_content = content[0].get("text", "")
                            return {
                                'success': True,
                                'content': text_content,
                                'language': 'en',  # Default, could be detected
                                'confidence': 0.9   # Default confidence
                            }
                        else:
                            return {
                                'success': False,
                                'error': 'No content in MCP response'
                            }
                    else:
                        return {
                            'success': False,
                            'error': response.get('error', 'Unknown MCP error')
                        }
                else:
                    return {
                        'success': False,
                        'error': f"MCP command failed: {result.stderr}"
                    }
                    
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'MCP server timeout'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'JSON decode error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'MCP server error: {str(e)}'
            }
    
    def test_connection(self):
        """Test MCP server connection"""
        try:
            # Simple test request
            test_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            result = self._call_mcp_server(test_request)
            return {
                'success': result.get('success', False),
                'message': 'MCP server connection test',
                'details': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'MCP connection test failed: {str(e)}'
            }


# Alternative simpler approach using direct MCP calls
class SimpleTikTokMCPClient:
    """Simplified MCP client using direct command calls"""
    
    def __init__(self, cache_dir="subtitle_cache"):
        self.server_path = "/Users/oliviachen/tiktok-mcp/build/index.js"
        self.api_key = "a8b6e7fcc74ca59cfbbff32b10f422f7"
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_filename(self, tiktok_url):
        """Generate cache filename from TikTok URL"""
        import hashlib
        url_hash = hashlib.md5(tiktok_url.encode()).hexdigest()
        # Extract video ID from URL for readability
        video_id = tiktok_url.split('/')[-1] if '/' in tiktok_url else url_hash[:8]
        return f"{self.cache_dir}/subtitles_{video_id}_{url_hash[:8]}.json"
    
    def _load_cached_subtitles(self, tiktok_url):
        """Load subtitles from cache if available"""
        cache_file = self._get_cache_filename(tiktok_url)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    cached_data['from_cache'] = True
                    return cached_data
            except Exception as e:
                print(f"Warning: Failed to load cache for {tiktok_url}: {e}")
        return None
    
    def _save_to_cache(self, tiktok_url, result):
        """Save subtitle result to cache"""
        cache_file = self._get_cache_filename(tiktok_url)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Cached subtitles to: {cache_file}")
        except Exception as e:
            print(f"Warning: Failed to cache subtitles for {tiktok_url}: {e}")
    
    def extract_subtitles(self, tiktok_url):
        """
        Extract subtitles using direct MCP command with caching
        """
        # Check cache first
        cached_result = self._load_cached_subtitles(tiktok_url)
        if cached_result:
            print(f"📁 Using cached subtitles for {tiktok_url}")
            return cached_result
        
        print(f"🔄 Extracting subtitles from API for {tiktok_url}")
        
        try:
            # Prepare MCP request as JSON-RPC
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "tiktok_get_subtitle",
                    "arguments": {
                        "tiktok_url": tiktok_url
                    }
                }
            }
            
            # Call the TikTok MCP server directly with JSON input
            cmd = ["node", self.server_path]
            
            env = os.environ.copy()
            env["TIKNEURON_MCP_API_KEY"] = self.api_key
            
            result = subprocess.run(
                cmd,
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            
            if result.returncode == 0:
                # Parse response - need to handle multiple JSON objects
                lines = result.stdout.strip().split('\n')
                response = None
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('TikTok MCP Server'):
                        try:
                            parsed = json.loads(line)
                            if 'result' in parsed:
                                response = parsed
                                break
                        except json.JSONDecodeError:
                            continue
                
                if response and "result" in response:
                    result_data = response["result"]
                    
                    # Check if it's an error response
                    if result_data.get("isError"):
                        content = result_data.get("content", [])
                        if content and len(content) > 0:
                            error_text = content[0].get("text", "Unknown error")
                            return {
                                'success': False,
                                'error': f"TikTok MCP API error: {error_text}",
                                'url': tiktok_url,
                                'api_error': True
                            }
                    
                    # Handle successful response formats
                    if "content" in result_data:
                        # Standard MCP content format
                        content = result_data["content"]
                        if content and len(content) > 0:
                            subtitle_text = content[0].get("text", "")
                            result = {
                                'success': True,
                                'subtitles': subtitle_text,
                                'url': tiktok_url,
                                'raw_response': response,
                                'from_cache': False
                            }
                            # Cache the successful result
                            self._save_to_cache(tiktok_url, result)
                            return result
                    elif isinstance(result_data, str):
                        # Direct string response
                        result = {
                            'success': True,
                            'subtitles': result_data,
                            'url': tiktok_url,
                            'raw_response': response,
                            'from_cache': False
                        }
                        # Cache the successful result
                        self._save_to_cache(tiktok_url, result)
                        return result
                
                return {
                    'success': False,
                    'error': 'No subtitle content found in response',
                    'url': tiktok_url,
                    'raw_response': response,
                    'stdout': result.stdout[:300],
                    'debug_lines': lines[:3]  # Show first few lines for debugging
                }
            else:
                return {
                    'success': False,
                    'error': f"Command failed: {result.stderr}",
                    'url': tiktok_url
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'MCP command timeout',
                'url': tiktok_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"MCP error: {str(e)}",
                'url': tiktok_url
            }
    
    def test_connection(self):
        """Test MCP server availability"""
        try:
            # Test if the server file exists
            if not os.path.exists(self.server_path):
                return {
                    'success': False,
                    'message': f'TikTok MCP server not found at {self.server_path}'
                }
            
            # Test simple tools/list request
            test_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            cmd = ["node", self.server_path]
            env = os.environ.copy()
            env["TIKNEURON_MCP_API_KEY"] = self.api_key
            
            result = subprocess.run(
                cmd,
                input=json.dumps(test_request),
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout)
                    return {
                        'success': True,
                        'message': 'TikTok MCP server is available',
                        'response': response
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'message': 'TikTok MCP server responded but output not JSON',
                        'stdout': result.stdout[:200]
                    }
            else:
                return {
                    'success': False,
                    'message': f'TikTok MCP server error: {result.stderr}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'MCP test failed: {str(e)}'
            }


# Example usage
if __name__ == "__main__":
    # Test both clients
    print("🧪 Testing TikTok MCP Clients")
    print("=" * 50)
    
    # Test simple client
    print("1. Testing Simple MCP Client...")
    simple_client = SimpleTikTokMCPClient()
    
    # Test connection
    conn_test = simple_client.test_connection()
    print(f"Connection test: {conn_test}")
    
    # Test with sample URL
    test_url = "https://www.tiktok.com/@8jelly8/video/7510593749152468255"
    print(f"\n2. Testing subtitle extraction with: {test_url}")
    
    result = simple_client.extract_subtitles(test_url)
    print(f"Result: {result}")