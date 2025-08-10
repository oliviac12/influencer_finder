"""
Creator Review App - Streamlit Interface
Batch AI-powered creator analysis and approval workflow
"""
import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from utils.content_database import ContentDatabase
from utils.ai_analysis_cache import AIAnalysisCache
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Creator Review System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CreatorReviewApp:
    def __init__(self):
        self.content_db = ContentDatabase()
        self.ai_cache = AIAnalysisCache()
        self.reviews_file = "creator_reviews.json"
        self.load_reviews()
        
    def load_reviews(self):
        """Load existing creator reviews"""
        if os.path.exists(self.reviews_file):
            with open(self.reviews_file, 'r') as f:
                self.reviews = json.load(f)
        else:
            self.reviews = {}
    
    def save_reviews(self):
        """Save creator reviews"""
        with open(self.reviews_file, 'w') as f:
            json.dump(self.reviews, f, indent=2)
    
    def get_creator_summary(self, username):
        """Get creator summary for AI analysis"""
        creator_data = self.content_db.get_creator_content(username)
        if not creator_data:
            return None
            
        profile = creator_data['profile']
        posts = creator_data['posts'][:10]  # Latest 10 posts
        
        summary = f"""
Creator: [@{username}](https://www.tiktok.com/@{username})
Nickname: {profile.get('nickname', 'N/A')}
Followers: {profile.get('followers', 0):,}
Bio: {profile.get('bio', 'N/A')}

Recent Posts Summary:
"""
        
        for i, post in enumerate(posts, 1):
            # Filter out None values from tags and ensure they're strings
            raw_tags = post.get('tags', []) or []
            clean_tags = [str(tag) for tag in raw_tags if tag is not None][:5]
            tags = ', '.join(clean_tags)
            
            # Create TikTok URL for the post
            post_id = post.get('id', '')
            post_url = f"https://www.tiktok.com/@{username}/video/{post_id}" if post_id else "URL not available"
            
            desc = (post.get('desc', '') or '')[:80]
            summary += f"{i}. {desc}..."
            if tags:
                summary += f" #{tags}"
            summary += f" ({post.get('likes', 0):,} likes) - [Link]({post_url})\n"
        
        return summary
    
    def analyze_creator_with_ai(self, username, campaign_brief, api_key):
        """Analyze creator using Claude API with caching"""
        # Check cache first
        cached_analysis = self.ai_cache.get_cached_analysis(username, campaign_brief)
        if cached_analysis:
            return f"{cached_analysis['analysis']}\n\n*💾 Using cached analysis from {cached_analysis['analyzed_at'][:10]}*"
        
        # If not cached, get creator summary for new analysis
        creator_summary = self.get_creator_summary(username)
        if not creator_summary:
            return "Error: Creator data not found"
        
        prompt = f"""
Based on the following creator data, analyze if this creator would be a good fit for a {campaign_brief} campaign:

{creator_summary}

Answer each question in 1-2 concise sentences, citing specific posts with URLs when relevant:

**Why is this creator a good match?**

**What topics does this creator talk about?**

**What brands or products does this creator talk about?**

**Do they create content about [key theme from your campaign]?**

**What's their content style and audience?**

**Overall Recommendation: Yes/No/Maybe**

Keep each answer brief (like the Radar example). When citing posts, use embedded links: "Post 3 discusses X [Link](https://www.tiktok.com/@username/video/123456)" or reference the post numbers from the summary above.
"""
        
        # Try to use Claude API
        try:
            # Get API key from environment variable
            claude_api_key = os.getenv('ANTHROPIC_API_KEY')
            if not claude_api_key:
                return "❌ **Error**: ANTHROPIC_API_KEY environment variable not set"
            
            client = anthropic.Anthropic(api_key=claude_api_key)
            
            # Use the modern API with Sonnet 4
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis_text = message.content[0].text
            
            # Extract recommendation from analysis
            recommendation = "Maybe"  # Default
            analysis_lower = analysis_text.lower()
            if "overall recommendation: yes" in analysis_lower or "recommendation**: yes" in analysis_lower:
                recommendation = "Yes"
            elif "overall recommendation: no" in analysis_lower or "recommendation**: no" in analysis_lower:
                recommendation = "No"
            
            # Cache the analysis
            self.ai_cache.save_analysis(username, campaign_brief, analysis_text, recommendation)
            
            return analysis_text
            
        except Exception as e:
            return f"❌ **Error calling Claude API**: {str(e)}"
    
    def batch_analyze_creators(self, creator_list, campaign_brief, api_key):
        """Analyze multiple creators in batch"""
        results = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, username in enumerate(creator_list):
            status_text.text(f"Analyzing @{username}... ({i+1}/{len(creator_list)})")
            progress_bar.progress((i + 1) / len(creator_list))
            
            analysis = self.analyze_creator_with_ai(username, campaign_brief, api_key)
            results[username] = analysis
            
            # Save analysis to session state
            st.session_state[f"batch_analysis_{username}"] = analysis
        
        status_text.text("✅ Analysis complete!")
        return results

def main():
    st.title("🎯 Creator Review System")
    st.markdown("**Batch AI-powered creator analysis workflow**")
    
    app = CreatorReviewApp()
    
    # Get creators from database
    try:
        with open("cache/creators_content_database.json", 'r') as f:
            database = json.load(f)
        creators_data = database.get('creators', {})
        creator_count = len(creators_data)
    except:
        st.error("Creator database not found. Run the screening process first.")
        return
    
    if creator_count == 0:
        st.error("No creators found in database. Run the screening process first.")
        return
    
    # Main interface
    st.header(f"📋 Campaign Analysis Setup")
    st.write(f"Database contains **{creator_count} creators** available for analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Campaign brief input
        campaign_brief = st.text_area(
            "Campaign Brief",
            value="fashion and lifestyle brand collaboration with focus on authentic content and strong engagement",
            height=100,
            help="Describe what you're looking for in creators for this campaign"
        )
        
        # Analysis mode selection
        st.subheader("👥 Analysis Mode")
        analysis_mode = st.radio(
            "Choose analysis mode:",
            ["🎯 Analyze Custom List", "🔍 Search Entire Database"],
            help="Choose whether to analyze specific creators or search your entire database"
        )
        
        selected_creators = []
        
        if analysis_mode == "🎯 Analyze Custom List":
            creator_input = st.text_area(
                "Paste Creator Usernames (one per line)",
                placeholder="username1\nusername2\nusername3\n...",
                height=150,
                help="Enter usernames without @ symbol, one per line"
            )
            if creator_input.strip():
                # Parse the input
                input_lines = [line.strip() for line in creator_input.strip().split('\n') if line.strip()]
                # Remove @ if present
                selected_creators = [username.lstrip('@') for username in input_lines]
                
                # Check which creators are in database
                found_creators = []
                missing_creators = []
                for username in selected_creators:
                    if username in creators_data:
                        found_creators.append(username)
                    else:
                        missing_creators.append(username)
                
                if found_creators:
                    st.success(f"✅ Found {len(found_creators)} creators in database: {', '.join(found_creators)}")
                if missing_creators:
                    st.warning(f"⚠️ {len(missing_creators)} creators not in database: {', '.join(missing_creators)}")
                
                selected_creators = found_creators
        
        else:  # Search Entire Database
            st.info("📋 Will analyze ALL creators in database")
            selected_creators = list(creators_data.keys())
        
        # API key is now hardcoded
        claude_api_key = "configured"  # Always available
    
    with col2:
        st.metric("Creators in Database", creator_count)
        if selected_creators:
            st.metric("Selected for Analysis", len(selected_creators))
        
        # Analysis button
        analyze_disabled = not claude_api_key or not selected_creators
        if analysis_mode == "🎯 Analyze Custom List":
            button_text = f"🚀 **Analyze {len(selected_creators)} Selected Creators**" if selected_creators else "🚀 **Paste Creator List First**"
        else:
            button_text = f"🚀 **Analyze All {len(selected_creators)} Creators**"
        
        if st.button(button_text, type="primary", disabled=not selected_creators):
            if not selected_creators:
                st.error("Please select creators to analyze first")
            else:
                st.write(f"🤖 **Starting analysis of {len(selected_creators)} creators...**")
                results = app.batch_analyze_creators(selected_creators, campaign_brief, claude_api_key)
                st.success("✅ **Analysis complete! Results below:**")
        
        if not selected_creators:
            st.info("💡 Select creators to analyze")
    
    # Show results if analysis has been run
    if any(key.startswith("batch_analysis_") for key in st.session_state.keys()):
        st.header("📊 Analysis Results")
        
        # Filter options
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            min_followers = st.number_input("Min Followers", min_value=0, value=0, step=1000)
        with col_b:
            show_filter = st.selectbox("Show", ["All", "Recommended", "Maybe", "Not Recommended"])
        with col_c:
            sort_by = st.selectbox("Sort by", ["Followers", "Username"])
        
        # Get analyzed creators
        analyzed_creators = []
        for username, data in creators_data.items():
            if f"batch_analysis_{username}" in st.session_state:
                profile = data.get('profile', {})
                followers = profile.get('followers', 0)
                
                # Apply follower filter
                if followers >= min_followers:
                    analysis = st.session_state[f"batch_analysis_{username}"]
                    
                    # Determine recommendation from analysis
                    analysis_lower = analysis.lower()
                    if "overall recommendation: yes" in analysis_lower or "recommendation**: yes" in analysis_lower:
                        recommendation = "Recommended"
                    elif "overall recommendation: no" in analysis_lower or "recommendation**: no" in analysis_lower:
                        recommendation = "Not Recommended"
                    else:
                        recommendation = "Maybe"
                    
                    # Apply recommendation filter
                    if show_filter == "All" or show_filter == recommendation:
                        analyzed_creators.append((username, data, analysis, recommendation, followers))
        
        # Sort creators
        if sort_by == "Followers":
            analyzed_creators.sort(key=lambda x: x[4], reverse=True)
        else:
            analyzed_creators.sort(key=lambda x: x[0])
        
        st.write(f"**Showing {len(analyzed_creators)} creators**")
        
        # Display results
        for username, creator_data, analysis, recommendation, followers in analyzed_creators:
            profile = creator_data.get('profile', {})
            posts = creator_data.get('posts', [])
            
            # Color code based on recommendation
            if recommendation == "Recommended":
                container_color = "🟢"
            elif recommendation == "Maybe":
                container_color = "🟡"
            else:
                container_color = "🔴"
            
            with st.expander(f"{container_color} @{username} - {recommendation} ({followers:,} followers)"):
                col_info, col_analysis, col_decision = st.columns([1, 2, 1])
                
                with col_info:
                    st.write(f"**Nickname:** {profile.get('nickname', 'N/A')}")
                    st.write(f"**Followers:** {followers:,}")
                    st.write(f"**Bio:** {profile.get('bio', 'N/A')[:100]}...")
                    st.write(f"**Posts in DB:** {len(posts)}")
                    
                    # Recent hashtags
                    recent_tags = []
                    for post in posts[:5]:
                        post_tags = post.get('tags', []) or []
                        # Filter out None values and convert to strings
                        clean_post_tags = [str(tag) for tag in post_tags if tag is not None]
                        recent_tags.extend(clean_post_tags)
                    top_tags = list(set(recent_tags))[:6]
                    if top_tags:
                        st.write(f"**Recent Tags:** {', '.join(f'#{tag}' for tag in top_tags)}")
                
                with col_analysis:
                    st.write("**🤖 AI Analysis:**")
                    st.write(analysis)
                
                with col_decision:
                    st.write("**Decision:**")
                    
                    # Current review status
                    current_review = app.reviews.get(username, {})
                    current_status = current_review.get('status', 'Not Reviewed')
                    
                    if current_status != 'Not Reviewed':
                        if current_status == 'Approved':
                            st.success(f"✅ {current_status}")
                        elif current_status == 'Rejected':
                            st.error(f"❌ {current_status}")
                        else:
                            st.warning(f"🤔 {current_status}")
                    
                    # Decision buttons
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        if st.button("✅", key=f"approve_{username}", help="Approve"):
                            app.reviews[username] = {
                                'status': 'Approved',
                                'timestamp': datetime.now().isoformat(),
                                'campaign_brief': campaign_brief,
                                'analysis': analysis,
                                'recommendation': recommendation
                            }
                            app.save_reviews()
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("🤔", key=f"maybe_{username}", help="Maybe"):
                            app.reviews[username] = {
                                'status': 'Maybe',
                                'timestamp': datetime.now().isoformat(),
                                'campaign_brief': campaign_brief,
                                'analysis': analysis,
                                'recommendation': recommendation
                            }
                            app.save_reviews()
                            st.rerun()
                    
                    with col_btn3:
                        if st.button("❌", key=f"reject_{username}", help="Reject"):
                            app.reviews[username] = {
                                'status': 'Rejected',
                                'timestamp': datetime.now().isoformat(),
                                'campaign_brief': campaign_brief,
                                'analysis': analysis,
                                'recommendation': recommendation
                            }
                            app.save_reviews()
                            st.rerun()
        
        # Export section
        st.header("📥 Export Results")
        
        # Count decisions
        approved = len([r for r in app.reviews.values() if r.get('status') == 'Approved'])
        maybe = len([r for r in app.reviews.values() if r.get('status') == 'Maybe'])
        rejected = len([r for r in app.reviews.values() if r.get('status') == 'Rejected'])
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("✅ Approved", approved)
        with col_stat2:
            st.metric("🤔 Maybe", maybe)
        with col_stat3:
            st.metric("❌ Rejected", rejected)
        with col_stat4:
            if st.button("📄 Export Approved"):
                approved_creators = [
                    username for username, review in app.reviews.items()
                    if review.get('status') == 'Approved'
                ]
                
                if approved_creators:
                    export_data = []
                    for username in approved_creators:
                        creator_data = app.content_db.get_creator_content(username)
                        if creator_data:
                            profile = creator_data['profile']
                            export_data.append({
                                'username': username,
                                'nickname': profile.get('nickname', ''),
                                'followers': profile.get('followers', 0),
                                'bio': profile.get('bio', ''),
                                'ai_recommendation': app.reviews[username].get('recommendation', ''),
                                'review_timestamp': app.reviews[username].get('timestamp', ''),
                            })
                    
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download Approved Creators CSV",
                        data=csv,
                        file_name=f"approved_creators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No approved creators to export")

if __name__ == "__main__":
    main()