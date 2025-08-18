# Architecture Improvement TODOs

## Critical Issues to Address

### 1. **Split Codebase Problem**
**Issue**: Streamlit app and email scheduler are in separate codebases (Streamlit Cloud vs Replit)
**Current Pain Points**:
- Manual file syncing required for attachments
- Code duplication between platforms
- Difficult to maintain consistency
- Deployment complexity

**Proposed Solutions**:
- Option A: Move everything to single platform (Streamlit Cloud with background jobs)
- Option B: Containerize both services and deploy together (Docker + Railway/Render)
- Option C: Use cloud storage for attachments (Supabase Storage, AWS S3)

### 2. **Attachment Storage Architecture**
**Issue**: Attachments stored locally, not accessible across platforms
**Current Workaround**: Manual file upload to Replit
**Better Solutions**:
- Supabase Storage integration
- AWS S3 or similar cloud storage
- Base64 encoding in database (for small files)

### 3. **Code Organization**
**Issue**: Utils and core logic scattered across different deployment targets
**Needs**:
- Shared package/module system
- Centralized configuration management
- Unified logging and monitoring

## Implementation Priority
1. **Immediate**: Use cloud storage for attachments (Supabase Storage)
2. **Medium-term**: Consolidate to single deployment platform
3. **Long-term**: Proper microservices architecture with shared packages

## Decision Criteria
- Development velocity vs maintenance overhead
- Cost considerations (Streamlit Cloud limits vs dedicated hosting)
- Scalability requirements for email volume
- Team size and DevOps capacity