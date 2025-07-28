# Data Directory

This directory contains all CSV data files used by the influencer finder system.

## Input Data (Raw datasets)
- **`data.csv`** - Sample creator dataset (10 creators for testing)
- **`radar_1k_10K_fashion_affiliate_5%_eng_rate.csv`** - Main dataset (351 fashion creators, 1K-10K followers, 5%+ engagement)

## Output Data (Generated results)
- **`qualified_creators.csv`** - Filtered creators that pass all screening criteria (engagement, recency, shoppable content)
- **`creator_lookup.csv`** - Generated lookup table with creator profile data
- **`creator_post_lookup.csv`** - Generated lookup table with creator post data

## File Relationships
```
Input datasets → screen_creators.py → qualified_creators.csv
                                   ↓
                              creator_lookup.csv + creator_post_lookup.csv
```

**Note:** The main screening process uses `radar_1k_10K_fashion_affiliate_5%_eng_rate.csv` as input and generates `qualified_creators.csv` as output.