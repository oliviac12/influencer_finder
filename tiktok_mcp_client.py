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
    
    def __init__(self):
        self.server_path = "/Users/oliviachen/tiktok-mcp/build/index.js"
        self.api_key = "9666be95906e253f99c347bfa7ccac4f"
    
    def extract_subtitles(self, tiktok_url):
        """
        Extract subtitles using direct MCP command
        """
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
                            return {
                                'success': True,
                                'subtitles': subtitle_text,
                                'url': tiktok_url,
                                'raw_response': response
                            }
                    elif isinstance(result_data, str):
                        # Direct string response
                        return {
                            'success': True,
                            'subtitles': result_data,
                            'url': tiktok_url,
                            'raw_response': response
                        }
                
                return {
                    'success': False,
                    'error': 'No subtitle content found in response',
                    'url': tiktok_url,
                    'raw_response': response,
                    'stdout': result.stdout[:300]
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