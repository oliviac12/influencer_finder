"""
Test TikTok MCP subtitle extraction
"""
import json
from tikapi_client import TikAPIClient
from tiktok_mcp_client import SimpleTikTokMCPClient

# Test configuration
API_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
TEST_USERNAME = "8jelly8"

def test_tiktok_mcp_subtitles():
    """Test TikTok MCP integration for subtitle extraction"""
    print("🧪 Testing TikTok MCP Subtitle Extraction")
    print("=" * 60)
    
    # Step 1: Test MCP connection
    print("1. Testing MCP connection...")
    mcp_client = SimpleTikTokMCPClient()
    conn_test = mcp_client.test_connection()
    
    if conn_test['success']:
        print(f"✅ MCP connection successful")
        print(f"   Available servers: {conn_test.get('servers', 'N/A')}")
    else:
        print(f"❌ MCP connection failed: {conn_test['message']}")
        print("   Make sure TikTok MCP server is configured and running")
        return
    
    # Step 2: Get creator posts using our TikAPI client
    print("\n2. Fetching creator posts...")
    tikapi_client = TikAPIClient(API_KEY)
    result = tikapi_client.get_creator_analysis(TEST_USERNAME, post_count=3)
    
    if not result['success']:
        print(f"❌ Failed to get creator data: {result['error']}")
        return
    
    profile = result['profile']
    posts = result['posts']
    
    print(f"✅ Found {len(posts)} posts for @{profile['username']} ({profile['nickname']})")
    
    # Step 3: Extract subtitles for each post
    print(f"\n3. Extracting subtitles using TikTok MCP...")
    
    results = []
    for i, post in enumerate(posts, 1):
        print(f"\n--- Post {i} ---")
        print(f"Description: {post['description'][:100]}...")
        print(f"TikTok URL: {post['tiktok_url']}")
        print(f"Duration: {post['duration']}s | Views: {post['stats']['views']:,}")
        
        # Extract subtitles using MCP
        subtitle_result = mcp_client.extract_subtitles(post['tiktok_url'])
        
        if subtitle_result['success']:
            subtitles = subtitle_result['subtitles']
            print(f"✅ Subtitles extracted ({len(subtitles)} chars)")
            print(f"   Preview: {subtitles[:200]}{'...' if len(subtitles) > 200 else ''}")
            
            # Store result for analysis
            results.append({
                'post': post,
                'subtitles': subtitles,
                'success': True
            })
        else:
            print(f"❌ Subtitle extraction failed: {subtitle_result['error']}")
            results.append({
                'post': post,
                'error': subtitle_result['error'],
                'success': False
            })
    
    return results

def test_mcp_call(tiktok_url):
    """
    Test MCP call structure for TikTok subtitle extraction
    This is a placeholder for the actual MCP integration
    """
    print(f"📝 Testing MCP call for: {tiktok_url}")
    
    # Expected MCP call structure (based on typical MCP patterns):
    # mcp_call = {
    #     "method": "extract_subtitles",
    #     "params": {
    #         "url": tiktok_url,
    #         "format": "text"  # or "srt", "vtt"
    #     }
    # }
    
    print("   🔄 MCP Call Structure:")
    print("   {")
    print(f'     "method": "extract_subtitles",')
    print("     \"params\": {")
    print(f'       "url": "{tiktok_url}",')
    print('       "format": "text"')
    print("     }")
    print("   }")
    
    # Simulate response
    print("   📄 Expected Response:")
    print("   {")
    print('     "success": true,')
    print('     "subtitles": "This is the extracted subtitle text...",')
    print('     "language": "en",')
    print('     "confidence": 0.95')
    print("   }")
    
    print("   ⚠️  Actual MCP integration needed here")

def test_with_sample_urls():
    """Test with some sample TikTok URLs to verify MCP structure"""
    print("\n3. Testing with sample URLs...")
    
    sample_urls = [
        "https://www.tiktok.com/@8jelly8/video/7510593749152468255",
        "https://www.tiktok.com/@8jelly8/video/7517042327047720223"
    ]
    
    for url in sample_urls:
        print(f"\n📎 Sample URL: {url}")
        test_mcp_call(url)

if __name__ == "__main__":
    results = test_tiktok_mcp_subtitles()
    
    if results:
        print("\n" + "=" * 60)
        print("📊 Summary Results:")
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"✅ Successful extractions: {len(successful)}")
        print(f"❌ Failed extractions: {len(failed)}")
        
        if successful:
            print(f"\n📝 Subtitle Preview from {len(successful)} posts:")
            for i, result in enumerate(successful, 1):
                post = result['post']
                subtitles = result['subtitles']
                print(f"\n{i}. @{TEST_USERNAME} - Post {post['id']}")
                print(f"   Description: {post['description'][:80]}...")
                print(f"   Subtitles ({len(subtitles)} chars): {subtitles[:150]}...")
        
        print("\n🔧 Next Steps:")
        print("1. ✅ TikAPI integration working")
        print("2. ✅ MCP client structure ready")
        print("3. 🔄 Test actual MCP subtitle extraction")
        print("4. ⏳ Integrate with LLM for content analysis")
    else:
        print("\n❌ No results to analyze. Check MCP server configuration.")