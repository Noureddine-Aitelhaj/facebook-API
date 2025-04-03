# Facebook Ads Library API Integration

This application provides a REST API interface to the Facebook Ads Library API, using Facebook's official [Ad-Library-API-Script-Repository](https://github.com/facebookresearch/Ad-Library-API-Script-Repository). It allows searching for ads using various criteria and returns the results in JSON or CSV format.

## API Endpoints

### 1. Status Check
- **URL**: `/`
- **Method**: `GET`
- **Description**: Check if the API is online

### 2. Search Ads
- **URL**: `/api/search`
- **Method**: `POST`
- **Description**: Search for ads in the Facebook Ads Library
- **Required Parameters**:
  - `access_token`: Facebook developer access token
  - `fields`: Comma-separated list of fields to retrieve
  - `country`: Comma-separated list of country codes
- **Optional Parameters**:
  - `search_term`: Term to search for (required if search_page_ids not provided)
  - `search_page_ids`: Specific Facebook Page IDs to search (required if search_term not provided)
  - `ad_active_status`: Filter by ad status (ALL, ACTIVE, INACTIVE)
  - `after_date`: Only return ads that started delivery after this date (YYYY-MM-DD)
  - `batch_size`: Number of ads to retrieve per request
  - `output_format`: 'json' or 'csv' (default: json)
  - `retry_limit`: Number of retries for failed requests (default: 3)

### 3. Count Ads
- **URL**: `/api/count`
- **Method**: `POST`
- **Description**: Count the number of ads matching the search criteria
- **Parameters**: Same as Search Ads endpoint

### 4. Ad Start Time Trending
- **URL**: `/api/trending`
- **Method**: `POST`
- **Description**: Get trending data for ad start times
- **Parameters**: Same as Search Ads endpoint
- **Returns**: Count of ads grouped by start date

### 5. Available Fields
- **URL**: `/api/fields`
- **Method**: `GET`
- **Description**: Get a list of all available fields that can be requested

### 6. Available Operators
- **URL**: `/api/operators`
- **Method**: `GET`
- **Description**: Get a list of all available operators that can be used with the API

## Getting Started

### Prerequisites
- Facebook Developer Account with access to the Ads Library API
- Facebook Developer Access Token

### Usage Example

```bash
# Search for ads with curl
curl -X POST https://facebookAPI.autoflowexperts.com/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "YOUR_FACEBOOK_ACCESS_TOKEN",
    "fields": "ad_creative_body,ad_creative_link_title,ad_delivery_start_time,page_name",
    "country": "US",
    "search_term": "climate change",
    "after_date": "2023-01-01",
    "output_format": "json"
  }'

# Count ads matching criteria
curl -X POST https://facebookAPI.autoflowexperts.com/api/count \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "YOUR_FACEBOOK_ACCESS_TOKEN",
    "fields": "ad_creative_body",
    "country": "US",
    "search_term": "climate change"
  }'

# Get trending data
curl -X POST https://facebookAPI.autoflowexperts.com/api/trending \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "YOUR_FACEBOOK_ACCESS_TOKEN",
    "fields": "ad_creative_body",
    "country": "US",
    "search_term": "climate change",
    "after_date": "2023-01-01"
  }'
