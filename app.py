#!/usr/bin/env python3
import os
import json
import tempfile
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# Import the Facebook Ads Library API utility functions from the official repo
# These imports will work because we've installed the package from GitHub
from fb_ads_library_api import FbAdsLibraryTraversal
from fb_ads_library_api_utils import get_country_code, is_valid_fields, valid_query_fields
from fb_ads_library_api_operators import save_to_csv, get_operators, count_ads, count_start_time_trending

app = Flask(__name__)
CORS(app)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Facebook Ads Library API Endpoint",
        "documentation": "See README for usage details",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/search', methods=['POST'])
def search_ads():
    """
    Search for ads in the Facebook Ads Library
    Required parameters:
    - access_token: Facebook developer access token
    - fields: Comma-separated list of fields to retrieve
    - country: Comma-separated list of country codes
    
    Optional parameters:
    - search_term: Term to search for (required if search_page_ids not provided)
    - search_page_ids: Specific Facebook Page IDs to search (required if search_term not provided)
    - ad_active_status: Filter by ad status (ALL, ACTIVE, INACTIVE)
    - after_date: Only return ads that started delivery after this date (YYYY-MM-DD)
    - batch_size: Number of ads to retrieve per request
    - output_format: 'json' or 'csv' (default: json)
    """
    try:
        data = request.json
        
        # Validate required parameters
        required_params = ['access_token', 'fields', 'country']
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing required parameter: {param}"}), 400
        
        # Validate that at least one search parameter is provided
        if 'search_term' not in data and 'search_page_ids' not in data:
            return jsonify({"error": "At least one of search_term or search_page_ids must be provided"}), 400
            
        # Validate fields
        fields = data['fields']
        fields_list = [field.strip() for field in fields.split(',') if field.strip()]
        invalid_fields = [field for field in fields_list if not is_valid_fields(field)]
        if invalid_fields:
            return jsonify({"error": f"Invalid fields: {', '.join(invalid_fields)}"}), 400
            
        # Validate country codes
        country_input = data['country']
        country_list = [country.strip() for country in country_input.split(',') if country.strip()]
        valid_country_codes = [get_country_code(c) for c in country_list]
        invalid_countries = [country for country, code in zip(country_list, valid_country_codes) if code is None]
        
        if invalid_countries:
            return jsonify({"error": f"Invalid/unsupported country codes: {', '.join(invalid_countries)}"}), 400
        
        # Set up parameters for the API
        search_term = data.get('search_term', '.')
        country_codes = ','.join([code for code in valid_country_codes if code is not None])
        search_page_ids = data.get('search_page_ids', '')
        ad_active_status = data.get('ad_active_status', 'ALL')
        after_date = data.get('after_date', '1970-01-01')
        batch_size = int(data.get('batch_size', 500))
        output_format = data.get('output_format', 'json')
        retry_limit = int(data.get('retry_limit', 3))
        
        # Initialize the API traversal
        api = FbAdsLibraryTraversal(
            data['access_token'],
            fields,
            search_term,
            country_codes,
            search_page_ids=search_page_ids,
            ad_active_status=ad_active_status,
            after_date=after_date,
            page_limit=batch_size,
            retry_limit=retry_limit
        )
        
        # Fetch the data
        generator_ad_archives = api.generate_ad_archives()
        
        # Process the results based on output format
        if output_format.lower() == 'csv':
            # Create a temporary file to store the CSV
            temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
            try:
                # Use the official save_to_csv operator
                save_to_csv(generator_ad_archives, [temp_file.name], fields, is_verbose=False)
                with open(temp_file.name, 'r') as f:
                    csv_data = f.read()
                return csv_data, 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=facebook_ads.csv'}
            finally:
                # Clean up the temporary file
                os.unlink(temp_file.name)
        else:
            # Return as JSON
            results = []
            ad_count = 0
            for ad_archives in generator_ad_archives:
                results.extend(ad_archives)
                ad_count += len(ad_archives)
                # Limit to 10,000 ads for API response to prevent timeouts
                if ad_count >= 10000:
                    break
            
            return jsonify({
                "ads": results,
                "count": len(results),
                "truncated": ad_count >= 10000,
                "search_parameters": {
                    "fields": fields_list,
                    "countries": country_list,
                    "search_term": search_term if search_term != '.' else None,
                    "search_page_ids": search_page_ids or None,
                    "ad_active_status": ad_active_status,
                    "after_date": after_date,
                }
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/count', methods=['POST'])
def count_ads_endpoint():
    """
    Count the number of ads matching the search criteria
    Required parameters are the same as search endpoint
    """
    try:
        data = request.json
        
        # Validate required parameters
        required_params = ['access_token', 'fields', 'country']
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing required parameter: {param}"}), 400
        
        # Validate that at least one search parameter is provided
        if 'search_term' not in data and 'search_page_ids' not in data:
            return jsonify({"error": "At least one of search_term or search_page_ids must be provided"}), 400
        
        # Set up parameters for the API
        search_term = data.get('search_term', '.')
        country_codes = data['country']
        fields = data['fields']
        search_page_ids = data.get('search_page_ids', '')
        ad_active_status = data.get('ad_active_status', 'ALL')
        after_date = data.get('after_date', '1970-01-01')
        batch_size = int(data.get('batch_size', 500))
        retry_limit = int(data.get('retry_limit', 3))
        
        # Initialize the API traversal
        api = FbAdsLibraryTraversal(
            data['access_token'],
            fields,
            search_term,
            country_codes,
            search_page_ids=search_page_ids,
            ad_active_status=ad_active_status,
            after_date=after_date,
            page_limit=batch_size,
            retry_limit=retry_limit
        )
        
        # Use the count operator
        generator_ad_archives = api.generate_ad_archives()
        count = 0
        for ad_archives in generator_ad_archives:
            count += len(ad_archives)
        
        return jsonify({
            "count": count,
            "search_parameters": {
                "search_term": search_term if search_term != '.' else None,
                "countries": country_codes,
                "search_page_ids": search_page_ids or None,
                "ad_active_status": ad_active_status,
                "after_date": after_date,
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trending', methods=['POST'])
def start_time_trending():
    """
    Get trending data for ad start times
    Required parameters are the same as search endpoint
    Returns a count of ads grouped by start date
    """
    try:
        data = request.json
        
        # Validate required parameters
        required_params = ['access_token', 'fields', 'country']
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing required parameter: {param}"}), 400
        
        # Validate that at least one search parameter is provided
        if 'search_term' not in data and 'search_page_ids' not in data:
            return jsonify({"error": "At least one of search_term or search_page_ids must be provided"}), 400
        
        # Set up parameters for the API
        search_term = data.get('search_term', '.')
        country_codes = data['country']
        fields = "ad_delivery_start_time," + data['fields']  # Ensure we get start time
        search_page_ids = data.get('search_page_ids', '')
        ad_active_status = data.get('ad_active_status', 'ALL')
        after_date = data.get('after_date', '1970-01-01')
        batch_size = int(data.get('batch_size', 500))
        retry_limit = int(data.get('retry_limit', 3))
        
        # Initialize the API traversal
        api = FbAdsLibraryTraversal(
            data['access_token'],
            fields,
            search_term,
            country_codes,
            search_page_ids=search_page_ids,
            ad_active_status=ad_active_status,
            after_date=after_date,
            page_limit=batch_size,
            retry_limit=retry_limit
        )
        
        # Create a temporary file for the trending data
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        try:
            # Fetch and process trending data using the official function
            generator_ad_archives = api.generate_ad_archives()
            count_start_time_trending(generator_ad_archives, [temp_file.name], is_verbose=False)
            
            # Read the CSV and convert to JSON
            trending_data = []
            with open(temp_file.name, 'r') as f:
                # Skip header line
                next(f)
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        date = parts[0].strip()
                        count = int(parts[1].strip())
                        trending_data.append({"date": date, "count": count})
        
            return jsonify({
                "trending_data": trending_data,
                "total_count": sum(item["count"] for item in trending_data),
                "search_parameters": {
                    "search_term": search_term if search_term != '.' else None,
                    "countries": country_codes,
                    "search_page_ids": search_page_ids or None,
                    "ad_active_status": ad_active_status,
                    "after_date": after_date,
                }
            })
        finally:
            # Clean up the temporary file
            os.unlink(temp_file.name)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fields', methods=['GET'])
def get_available_fields():
    """Return the list of available fields that can be requested from the API"""
    return jsonify({
        "fields": valid_query_fields,
        "description": "These fields can be requested from the Facebook Ads Library API"
    })

@app.route('/api/operators', methods=['GET'])
def get_available_operators():
    """Return the list of available operators for the Facebook Ad Library API"""
    operators = get_operators()
    return jsonify({
        "operators": list(operators.keys()),
        "description": "These operators can be used with the Facebook Ads Library API"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
