"""
Creator Review App - Streamlit Interface
Batch AI-powered creator analysis and approval workflow
"""
import streamlit as st
import json
import os
import sys
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.content_database import ContentDatabase
from utils.ai_analysis_cache import AIAnalysisCache
from utils.human_review_cache import HumanReviewCache
from utils.email_cache import EmailCache
from utils.campaign_manager import CampaignManager
import anthropic
from dotenv import load_dotenv
from email_outreach import render_email_outreach_section
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

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
        self.human_cache = HumanReviewCache()
        self.email_cache = EmailCache()
        self.campaign_manager = CampaignManager()
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
    
    def analyze_creator_with_ai(self, username, campaign_name, campaign_brief, api_key):
        """Analyze creator using Claude API with caching"""
        # Check cache first
        cached_analysis = self.ai_cache.get_cached_analysis(username, campaign_name)
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
            try:
                self.ai_cache.save_analysis(username, campaign_name, campaign_brief, analysis_text, recommendation)
            except TypeError as e:
                st.error(f"Cache save error: {e}")
                st.error(f"Arguments: username={username}, campaign_name={campaign_name}, brief_len={len(campaign_brief)}, analysis_len={len(analysis_text)}, rec={recommendation}")
            
            return analysis_text
            
        except Exception as e:
            return f"❌ **Error calling Claude API**: {str(e)}"
    
    def extract_and_cache_email(self, username):
        """Extract email from creator's bio and update the database"""
        try:
            creator_data = self.content_db.get_creator_content(username)
            if not creator_data:
                return None
            
            profile = creator_data.get('profile', {})
            bio = profile.get('bio', '') or ''
            
            # Simple email extraction from bio
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, bio)
            
            if emails:
                # Take the first email found
                email = emails[0].lower()
                
                # Update the profile in the database - direct approach
                profile['email'] = email
                
                # Load database directly and update
                db = self.content_db.load_database()
                if username in db["creators"]:
                    db["creators"][username]["profile"] = profile
                    db["metadata"]["last_updated"] = datetime.now().isoformat()
                    self.content_db.save_database(db)
                
                return email
            
            return None
            
        except Exception as e:
            st.error(f"Error extracting email for @{username}: {str(e)}")
            return None
    
    def generate_personalized_email(self, username, campaign_name, campaign_brief):
        """Generate personalized outreach email for a creator"""
        try:
            # Check persistent email cache first
            cached_email = self.email_cache.get_email(username, campaign_name)
            if cached_email:
                return cached_email
            
            # Get cached analysis for context
            cached_analysis = self.ai_cache.get_cached_analysis(username, campaign_name)
            if not cached_analysis:
                return "No analysis available for personalization"
            
            analysis_text = cached_analysis.get('analysis', '')
            
            # Get creator data for additional context
            creator_data = self.content_db.get_creator_content(username)
            if not creator_data:
                return "Creator data not found"
            
            profile = creator_data.get('profile', {})
            nickname = profile.get('nickname', username)
            
            # Generate email using Claude
            prompt = f"""
Based on this creator analysis, write a brief, personalized outreach email from Wonder (a brand) to @{username}.

Creator Analysis:
{analysis_text}

Campaign Brief: {campaign_brief}

Write a 3-4 sentence email that:
1. Opens with something specific about their content (reference a specific post or theme from the analysis)
2. Briefly introduces Wonder and why they're a good fit
3. Proposes a collaboration
4. Keeps it casual and authentic (not overly formal)

Start with "Hi {nickname}," and sign off with "Best, [Your Name] from Wonder"

Keep it under 100 words. Be specific and personal, not generic.
"""
            
            claude_api_key = os.getenv('ANTHROPIC_API_KEY')
            if not claude_api_key:
                return "API key not configured"
            
            client = anthropic.Anthropic(api_key=claude_api_key)
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            email_text = message.content[0].text.strip()
            
            # Save to persistent cache
            self.email_cache.save_email(username, campaign_name, email_text)
            
            return email_text
            
        except Exception as e:
            return f"Error generating email: {str(e)}"
    
    def batch_analyze_creators(self, creator_list, campaign_name, campaign_brief, api_key):
        """Analyze multiple creators in parallel"""
        results = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def analyze_single_creator(username):
            return username, self.analyze_creator_with_ai(username, campaign_name, campaign_brief, api_key)
        
        # Use ThreadPoolExecutor for parallel processing
        # Limit to 3-5 concurrent threads to avoid rate limits
        max_workers = min(3, len(creator_list))
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_username = {
                executor.submit(analyze_single_creator, username): username 
                for username in creator_list
            }
            
            # Process completed tasks as they finish
            for future in as_completed(future_to_username):
                username = future_to_username[future]
                try:
                    username, analysis = future.result()
                    results[username] = analysis
                    
                    # Save analysis to session state
                    st.session_state[f"batch_analysis_{username}"] = analysis
                    
                    completed_count += 1
                    progress_bar.progress(completed_count / len(creator_list))
                    status_text.text(f"Completed: {completed_count}/{len(creator_list)} creators")
                    
                except Exception as e:
                    st.error(f"Error analyzing @{username}: {str(e)}")
                    results[username] = f"❌ Error: {str(e)}"
        
        status_text.text("✅ Analysis complete!")
        return results

def main():
    st.title("🎯 Creator Review System")
    st.markdown("**Batch AI-powered creator analysis workflow**")
    
    app = CreatorReviewApp()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Creator Analysis", "📧 Email Outreach", "💬 Reply Management"])
    
    with tab1:
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
        
        # Campaign Management Section
        st.subheader("🎯 Campaign Management")
        col_name, col_brief = st.columns([1, 2])
        
        with col_name:
            # Campaign selection/creation - check all sources
            campaigns_from_ai = set([v.get('campaign_name', '') for v in app.ai_cache.load_cache().values() if v.get('campaign_name')])
            campaigns_from_human = set([v.get('campaign_name', '') for v in app.human_cache.cache.values() if v.get('campaign_name')])
            campaigns_from_manager = set(app.campaign_manager.get_all_campaign_names())
            all_campaigns = campaigns_from_ai.union(campaigns_from_human).union(campaigns_from_manager)
            existing_campaigns = sorted([c for c in all_campaigns if c])  # Remove empty strings and sort
            
            if existing_campaigns:
                campaign_options = ["➕ Create New Campaign"] + existing_campaigns
                selected_option = st.selectbox("Select Campaign", campaign_options, key="campaign_selector")
                
                if selected_option == "➕ Create New Campaign":
                    campaign_name = st.text_input("Campaign Name", placeholder="e.g., Summer Travel 2024")
                    if campaign_name:
                        st.session_state.current_campaign = campaign_name
                else:
                    campaign_name = selected_option
                    st.info(f"📂 Using existing campaign: **{campaign_name}**")
                    
                    # Store campaign name in session state for access across tabs
                    st.session_state.current_campaign = campaign_name
                    
                    # Store campaign name in session state to detect changes
                    if 'last_selected_campaign' not in st.session_state:
                        st.session_state.last_selected_campaign = campaign_name
                    elif st.session_state.last_selected_campaign != campaign_name:
                        # Campaign changed - clear the brief from session state to load new one
                        st.session_state.last_selected_campaign = campaign_name
                        if 'campaign_brief_text' in st.session_state:
                            del st.session_state['campaign_brief_text']
            else:
                campaign_name = st.text_input("Campaign Name", value="My First Campaign", placeholder="e.g., Summer Travel 2024")
                if campaign_name:
                    st.session_state.current_campaign = campaign_name
        
        with col_brief:
            # Initialize default brief
            default_brief = "fashion and lifestyle brand collaboration with focus on authentic content and strong engagement"
            
            # Determine what brief to show
            brief_to_show = default_brief
            
            # If existing campaign selected, load its brief
            if campaign_name and campaign_name != "➕ Create New Campaign":
                # Check if we need to load a new brief (either no brief in session or campaign changed)
                should_load_brief = (
                    'loaded_campaign_brief' not in st.session_state or
                    st.session_state.get('loaded_campaign_brief') != campaign_name
                )
                
                if should_load_brief:
                    # First check CampaignManager for the brief
                    saved_brief = app.campaign_manager.get_campaign_brief(campaign_name)
                    if saved_brief:
                        brief_to_show = saved_brief
                        st.session_state.loaded_campaign_brief = campaign_name
                    else:
                        # Fall back to looking in AI cache
                        ai_cache = app.ai_cache.load_cache()
                        for key, data in ai_cache.items():
                            if data.get('campaign_name') == campaign_name and data.get('campaign_brief'):
                                brief_to_show = data['campaign_brief']
                                # Also save it to CampaignManager for future use
                                app.campaign_manager.save_campaign(campaign_name, data['campaign_brief'])
                                st.session_state.loaded_campaign_brief = campaign_name
                                break
                else:
                    # Use the existing value if already loaded for this campaign
                    brief_to_show = st.session_state.get('campaign_brief_text', default_brief)
            
            # Campaign brief input
            campaign_brief = st.text_area(
                "Campaign Brief (can be modified anytime)",
                value=brief_to_show,
                height=100,
                help="Describe what you're looking for. You can update this without losing cached analyses.",
                key=f"campaign_brief_{campaign_name if campaign_name else 'default'}"
            )
            
            # Store the current brief in session state
            st.session_state.campaign_brief_text = campaign_brief
        
        # Show campaign stats if exists
        if campaign_name and campaign_name != "➕ Create New Campaign":
            stats = app.human_cache.get_campaign_stats(campaign_name)
            if stats['total_reviewed'] > 0:
                st.success(f"📊 **Campaign Progress**: {stats['total_reviewed']} reviewed | ✅ {stats['approved']} approved | ❌ {stats['rejected']} rejected | 🤔 {stats['maybe']} maybe")
            
            # Migration helper for legacy reviews
            legacy_count = len([r for r in app.reviews.values() if r.get('status') in ['Approved', 'Maybe', 'Rejected']])
            if legacy_count > 0:
                st.info(f"📋 Found {legacy_count} legacy reviews. When you see creators with legacy reviews, just click the decision buttons to migrate them to this campaign.")
                if st.button("🔄 Clear Legacy Cache (Start Fresh)", help="This will delete all legacy reviews to avoid confusion"):
                    app.reviews = {}
                    app.save_reviews()
                    st.success("✅ Legacy reviews cleared. All future reviews will use the new campaign system.")
                    st.rerun()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
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
            analyze_disabled = not claude_api_key or not selected_creators or not campaign_name or campaign_name == "➕ Create New Campaign"
            if analysis_mode == "🎯 Analyze Custom List":
                button_text = f"🚀 **Analyze {len(selected_creators)} Selected Creators**" if selected_creators else "🚀 **Paste Creator List First**"
            else:
                button_text = f"🚀 **Analyze All {len(selected_creators)} Creators**"
            
            if not campaign_name or campaign_name == "➕ Create New Campaign":
                st.warning("⚠️ Please create or select a campaign before analyzing")
            
            if st.button(button_text, type="primary", disabled=analyze_disabled):
                if not selected_creators:
                    st.error("Please select creators to analyze first")
                else:
                    # Save campaign and brief to CampaignManager
                    app.campaign_manager.save_campaign(campaign_name, campaign_brief)
                    
                    st.write(f"🤖 **Starting analysis of {len(selected_creators)} creators for campaign: {campaign_name}...**")
                    results = app.batch_analyze_creators(selected_creators, campaign_name, campaign_brief, claude_api_key)
                st.success("✅ **Analysis complete! Results below:**")
        
        if not selected_creators:
            st.info("💡 Select creators to analyze")
    
    # Show results if analysis has been run
    if any(key.startswith("batch_analysis_") for key in st.session_state.keys()):
        st.header("📊 Analysis Results")
        
        # Filter options
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            min_followers = st.number_input("Min Followers", min_value=0, value=0, step=1000)
        with col_b:
            show_filter = st.selectbox("AI Recommendation", ["All", "Recommended", "Maybe", "Not Recommended"])
        with col_c:
            review_status = st.selectbox("Review Status", ["All", "🆕 Unreviewed Only", "✅ Reviewed Only"])
        with col_d:
            sort_by = st.selectbox("Sort by", ["Review Status", "Followers", "Username"])
        
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
                    
                    # Check review status for this campaign
                    is_reviewed = False
                    if campaign_name and campaign_name != "➕ Create New Campaign":
                        human_review = app.human_cache.get_review(username, campaign_name)
                        is_reviewed = human_review is not None
                    
                    # Apply filters
                    passes_recommendation = (show_filter == "All" or show_filter == recommendation)
                    passes_review_status = (
                        review_status == "All" or
                        (review_status == "🆕 Unreviewed Only" and not is_reviewed) or
                        (review_status == "✅ Reviewed Only" and is_reviewed)
                    )
                    
                    if passes_recommendation and passes_review_status:
                        analyzed_creators.append((username, data, analysis, recommendation, followers, is_reviewed))
        
        # Sort creators
        if sort_by == "Review Status":
            # Sort unreviewed first, then by followers
            analyzed_creators.sort(key=lambda x: (x[5], -x[4]))  # is_reviewed=False comes first
        elif sort_by == "Followers":
            analyzed_creators.sort(key=lambda x: x[4], reverse=True)
        else:
            analyzed_creators.sort(key=lambda x: x[0])
        
        # Count reviewed vs unreviewed
        reviewed_count = sum(1 for c in analyzed_creators if c[5])
        unreviewed_count = len(analyzed_creators) - reviewed_count
        
        st.write(f"**Showing {len(analyzed_creators)} creators** (🆕 {unreviewed_count} unreviewed, ✅ {reviewed_count} reviewed)")
        
        # Display results with section headers if showing all
        last_review_status = None
        for username, creator_data, analysis, recommendation, followers, is_reviewed in analyzed_creators:
            # Add section header when review status changes
            if review_status == "All" and sort_by == "Review Status":
                if last_review_status is None and not is_reviewed:
                    st.markdown("### 🆕 Unreviewed Creators")
                elif last_review_status == False and is_reviewed:
                    st.markdown("---")
                    st.markdown("### ✅ Reviewed Creators")
                last_review_status = is_reviewed
            profile = creator_data.get('profile', {})
            posts = creator_data.get('posts', [])
            
            # Build status indicators
            ai_indicator = "🟢" if recommendation == "Recommended" else "🟡" if recommendation == "Maybe" else "🔴"
            review_indicator = "✅" if is_reviewed else "🆕"
            
            # Get human decision if reviewed
            human_decision = ""
            if is_reviewed and campaign_name and campaign_name != "➕ Create New Campaign":
                human_review = app.human_cache.get_review(username, campaign_name)
                if human_review:
                    decision = human_review['decision']
                    if decision == 'approved':
                        human_decision = " | ✅ Approved"
                    elif decision == 'rejected':
                        human_decision = " | ❌ Rejected"
                    else:
                        human_decision = " | 🤔 Maybe"
            
            with st.expander(f"{review_indicator} {ai_indicator} @{username} - AI: {recommendation} ({followers:,} followers){human_decision}"):
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
                    
                    # Check human review status for this campaign
                    if campaign_name and campaign_name != "➕ Create New Campaign":
                        human_review = app.human_cache.get_review(username, campaign_name)
                        if human_review:
                            decision = human_review['decision']
                            if decision == 'approved':
                                st.success(f"✅ Approved")
                                st.caption(f"Reviewed: {human_review['reviewed_at'][:10]}")
                            elif decision == 'rejected':
                                st.error(f"❌ Rejected")
                                st.caption(f"Reviewed: {human_review['reviewed_at'][:10]}")
                            else:
                                st.warning(f"🤔 Maybe")
                                st.caption(f"Reviewed: {human_review['reviewed_at'][:10]}")
                            
                            if human_review.get('notes'):
                                st.caption(f"Notes: {human_review['notes']}")
                        else:
                            # Check for legacy review
                            legacy_review = app.reviews.get(username)
                            if legacy_review and legacy_review.get('status') in ['Approved', 'Maybe', 'Rejected']:
                                st.warning(f"📋 Legacy Review: {legacy_review['status']}")
                                st.caption(f"From: {legacy_review.get('timestamp', '')[:10]}")
                                st.info("⬇️ Click a button below to migrate to current campaign")
                    
                    # Decision buttons
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        if st.button("✅", key=f"approve_{username}", help="Approve"):
                            if campaign_name and campaign_name != "➕ Create New Campaign":
                                # Extract and cache email on approval
                                extracted_email = app.extract_and_cache_email(username)
                                if extracted_email:
                                    st.success(f"✅ Email extracted: {extracted_email}")
                                
                                app.human_cache.save_review(username, campaign_name, 'approved', f"AI: {recommendation}")
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
                            if campaign_name and campaign_name != "➕ Create New Campaign":
                                # Extract and cache email on maybe decision too
                                extracted_email = app.extract_and_cache_email(username)
                                if extracted_email:
                                    st.success(f"📧 Email extracted: {extracted_email}")
                                
                                app.human_cache.save_review(username, campaign_name, 'maybe', f"AI: {recommendation}")
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
                            if campaign_name and campaign_name != "➕ Create New Campaign":
                                app.human_cache.save_review(username, campaign_name, 'rejected', f"AI: {recommendation}")
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
        
        # Count decisions for current campaign
        if campaign_name and campaign_name != "➕ Create New Campaign":
            campaign_reviews = app.human_cache.get_campaign_reviews(campaign_name)
            approved = sum(1 for r in campaign_reviews if r['decision'] == 'approved')
            maybe = sum(1 for r in campaign_reviews if r['decision'] == 'maybe')
            rejected = sum(1 for r in campaign_reviews if r['decision'] == 'rejected')
        else:
            # Fallback to legacy reviews
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
            if st.button("📄 Export Approved + Maybe"):
                # Get campaign-specific reviews
                if campaign_name and campaign_name != "➕ Create New Campaign":
                    campaign_reviews = app.human_cache.get_campaign_reviews(campaign_name)
                    exportable_creators = [
                        (r['username'], r) for r in campaign_reviews
                        if r['decision'] in ['approved', 'maybe']
                    ]
                else:
                    # Fallback to legacy reviews
                    exportable_creators = [
                        (username, review) for username, review in app.reviews.items()
                        if review.get('status') in ['Approved', 'Maybe']
                    ]
                
                if exportable_creators:
                    # Count how many emails are already cached
                    cached_count = sum(1 for username, _ in exportable_creators 
                                     if app.email_cache.has_email(username, campaign_name if campaign_name else "General"))
                    new_count = len(exportable_creators) - cached_count
                    
                    status_msg = f"Preparing emails ({cached_count} cached, {new_count} new to generate)..."
                    with st.spinner(status_msg):
                        export_data = []
                        email_progress = st.progress(0)
                        
                        for idx, (username, review) in enumerate(exportable_creators):
                            creator_data = app.content_db.get_creator_content(username)
                            if creator_data:
                                profile = creator_data['profile']
                                # Handle both new campaign format and legacy format
                                if 'decision' in review:  # New campaign format
                                    decision = review['decision'].title()  # approved -> Approved
                                    timestamp = review.get('reviewed_at', '')
                                else:  # Legacy format
                                    decision = review.get('status', '')
                                    timestamp = review.get('timestamp', '')
                                
                                # Generate or retrieve personalized email (cached automatically)
                                personalized_email = app.generate_personalized_email(
                                    username, 
                                    campaign_name if campaign_name else "General", 
                                    campaign_brief
                                )
                                
                                export_data.append({
                                    'username': username,
                                    'human_decision': decision,  # Shows Approved or Maybe
                                    'nickname': profile.get('nickname', ''),
                                    'followers': profile.get('followers', 0),
                                    'bio': profile.get('bio', ''),
                                    'campaign': campaign_name if campaign_name else 'Unknown',
                                    'personalized_email': personalized_email,
                                    'review_timestamp': timestamp,
                                })
                                
                                # Update progress
                                email_progress.progress((idx + 1) / len(exportable_creators))
                    
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    
                    # Include campaign name in filename if available
                    if campaign_name and campaign_name != "➕ Create New Campaign":
                        safe_campaign_name = campaign_name.lower().replace(' ', '_')
                        filename = f"{safe_campaign_name}_creators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    else:
                        filename = f"reviewed_creators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    
                    st.download_button(
                        label=f"📥 Download {len(exportable_creators)} Creators CSV",
                        data=csv,
                        file_name=filename,
                        mime="text/csv"
                    )
                else:
                    st.warning("No approved or maybe creators to export")
    
    # Email Outreach Tab
    with tab2:
        # Pass the current campaign from session state
        current_campaign = st.session_state.get('current_campaign', None)
        render_email_outreach_section(app, current_campaign)
    
    # Reply Management Tab
    with tab3:
        from reply_management import render_reply_management_section
        current_campaign = st.session_state.get('current_campaign', None)
        render_reply_management_section(app, current_campaign)

if __name__ == "__main__":
    main()