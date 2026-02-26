"""
AI-powered summarization using OpenAI API
"""
from openai import OpenAI
from django.conf import settings
import json
import re


def generate_text_summary(eo_data):
    """
    Generate AI summary of EO analysis results for a field

    Args:
        eo_data: Dict containing NDVI and ET data for a field

    Returns:
        Dict with trend_consistency, timing_alignment, continuity summaries
    """

    # Get API credentials
    api_key = settings.OPENAI_API_KEY
    base_url = settings.OPENAI_BASE_URL

    print(f"\n=== AI Summarization Debug ===")
    print(f"API Key (first 20 chars): {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    print(f"================================\n")

    # Extract key metrics from EO data
    ndvi_info = eo_data.get('NDVI', {})
    et_info = eo_data.get('ET', {})
    et_analysis = eo_data.get('et_analysis', {})
    vegetation_summary = eo_data.get('vegetation_summary', {})

    # Build a concise data summary
    data_summary = f"""
NDVI Data:
- NDVI Mean: {ndvi_info.get('ndvi_mean', 'N/A')}%
- Data points: {ndvi_info.get('data_points', [])}

ET Data:
- ET Mean: {et_info.get('et_mean', 'N/A')}%
- Data points: {et_info.get('data_points', [])}

ET Analysis Data:
- Total ET mm: {et_analysis.get('total_et_mm', 'N/A')} mm
- Mean Monthly ET mm: {et_analysis.get('mean_monthly_et_mm', 'N/A')}
- Max Monthly ET mm: {et_analysis.get('max_monthly_et_mm', 'N/A')}
- Min Monthly ET mm: {et_analysis.get('min_monthly_et_mm', 'N/A')}
- Peak ET Month:  {et_analysis.get('peak_et_month', 'N/A')}
- Total ET Inches: {et_analysis.get('total_et_inches', 'N/A')}  
- Growing Season ET mm: {et_analysis.get('growing_season_et_mm', 'N/A')}    
- Growing Season ET Inches:  {et_analysis.get('growing_season_et_inches', 'N/A')}    
- Date Range: {et_analysis.get('date_range', 'N/A')}          
- Yearly Totals mm": {et_analysis.get('yearly_totals_mm', 'N/A')}   
- seasonal totals mm: {et_analysis.get('seasonal_totals_mm', 'N/A')}              
- monthly trend:  {et_analysis.get('monthly_trend', 'N/A')}          
- trend slope mm per month: {et_analysis.get('trend_slope_mm_per_month', 'N/A')}       
- ET variability:  {et_analysis.get('et_variability', 'N/A')}  
- water use classification: {et_analysis.get('water_use_classification', 'N/A')}                 
- water use description:  {et_analysis.get('water_use_description', 'N/A')}          

Vegetation Summary
- Total observations: {vegetation_summary.get('total_observations', 'N/A')} mm
- Mean Monthly NDVI: {vegetation_summary.get('mean_ndvi', 'N/A')}
- Max NDVI: {vegetation_summary.get('max_ndvi', 'N/A')}
- Min NDVI: {vegetation_summary.get('min_ndvi', 'N/A')}
- DTS DEV:  {vegetation_summary.get('std_dev', 'N/A')}
- Vigor classification: {vegetation_summary.get('vigor_classification', 'N/A')}  
"""

    # Build prompt based on the document's guidelines
    prompt = f"""You are analyzing Earth observation data for agricultural conservation verification. 
Your role is to provide supporting context ONLY - not make determinations or judgments.


Earth Observation Data Summary:
{data_summary}

Based on this data, provide three brief summaries (2-3 sentences each):

1. TREND CONSISTENCY: Describe observable vegetation, water use, or land cover patterns over time. 
   Do NOT include thresholds, pass/fail language, or compliance statements.

2. TIMING ALIGNMENT: Describe when key events occurred (planting, cover crops, irrigation) compared to reported dates.
   Do NOT judge if timing was "correct" or "compliant".

3. CONTINUITY OVER TIME: Describe multi-year patterns showing practice persistence or rotation sequences.
   Do NOT make determinations about whether practices were "successful".

4. OVERALL SUMMARY: A brief 2-3 sentence summary of all observations.

Important: These summaries are SUPPORTING DOCUMENTATION ONLY. All determinations remain with NRCS conservationists.
Use neutral, observational language. Focus on "what was observed" not "what should have been".

Format your response as:

TREND_CONSISTENCY: [your analysis]

TIMING_ALIGNMENT: [your analysis]

CONTINUITY_OVER_TIME: [your analysis]

OVERALL_SUMMARY: [your summary]
"""

    try:
        print("Creating OpenAI client...")

        # Create client with only supported parameters
        client_params = {
            "api_key": api_key,
            "base_url": base_url
        }

        client = OpenAI(api_key=api_key, base_url=base_url)

        print("Sending request to OpenAI API...")

        # Try without response_format for NASA API compatibility
        response = client.chat.completions.create(
            model="claude-4-sonnet",
            messages=[
                {
                    "role": "system",
                    "content": "You are a neutral agricultural data analyst providing observational summaries for conservation verification. You never make determinations or compliance judgments."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )

        print("Received response from OpenAI API")
        content = response.choices[0].message.content
        print(f"Raw response content:\n{content}\n")

        # Parse the structured response
        result = parse_structured_response(content)
        print(f"Parsed result: {result}")
        return result

    except Exception as e:
        error_msg = str(e)
        print(f"AI summarization failed: {error_msg}")

        # Return a fallback response with actual data
        return generate_fallback_summary(eo_data, error_msg)


def parse_structured_response(content):
    """
    Parse the AI response into structured fields
    """
    result = {
        "trend_consistency": "",
        "timing_alignment": "",
        "continuity_over_time": "",
        "ai_summary": ""
    }

    # Try to extract sections using regex
    patterns = {
        "trend_consistency": r"TREND_CONSISTENCY:\s*(.+?)(?=TIMING_ALIGNMENT:|$)",
        "timing_alignment": r"TIMING_ALIGNMENT:\s*(.+?)(?=CONTINUITY_OVER_TIME:|$)",
        "continuity_over_time": r"CONTINUITY_OVER_TIME:\s*(.+?)(?=OVERALL_SUMMARY:|$)",
        "ai_summary": r"OVERALL_SUMMARY:\s*(.+?)$"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            result[key] = match.group(1).strip()

    # If parsing failed, try JSON parsing
    if not result["trend_consistency"]:
        try:
            json_result = json.loads(content)
            result.update(json_result)
        except:
            # Use the full content as summary
            result["ai_summary"] = content[:500] if content else "No response generated"
            result["trend_consistency"] = "See overall summary for details."
            result["timing_alignment"] = "See overall summary for details."
            result["continuity_over_time"] = "See overall summary for details."

    return result


def generate_fallback_summary(field_practice, eo_data, error_msg=""):
    """
    Generate a simple fallback summary based on the data without AI
    """
    practice_name = "Nothing"
    field_name = "Fake Field"

    # Extract some basic info
    landsat_info = eo_data.get('landsat', {})
    sentinel_info = eo_data.get('sentinel', {})
    openet_info = eo_data.get('openet', {})

    landsat_scenes = landsat_info.get('scenes_found', 0)
    sentinel_scenes = sentinel_info.get('scenes_found', 0)
    total_scenes = landsat_scenes + sentinel_scenes

    landsat_cloud = landsat_info.get('cloud_coverage_avg', 0)
    sentinel_cloud = sentinel_info.get('cloud_coverage_avg', 0)

    # Check data source
    landsat_source = landsat_info.get('metadata', {}).get('data_source', 'Unknown')
    using_real_data = 'USGS' in landsat_source or 'Planetary' in str(sentinel_info.get('metadata', {}))

    return {
        "trend_consistency": f"FALLBACK Earth observation data from {total_scenes} satellite scenes (Landsat: {landsat_scenes}, Sentinel-2: {sentinel_scenes}) covering field '{field_name}' shows observable patterns consistent with {practice_name} implementation. Average cloud cover of {landsat_cloud:.1f}% (Landsat) and {sentinel_cloud:.1f}% (Sentinel-2) provides adequate data quality for temporal analysis.",

        "timing_alignment": f"FALLBACK Multi-temporal satellite imagery captures seasonal changes aligned with typical {practice_name} schedules. Temporal coverage spans the implementation period with sufficient frequency for verification. Detailed timing analysis would require scene-by-scene review of acquisition dates.",

        "continuity_over_time": f"FALLBACK Satellite data archive for {field_name} provides baseline for assessing practice continuity. {'Real-time data from USGS and Copernicus systems' if using_real_data else 'Simulated data based on typical patterns'} enables multi-season pattern analysis. Long-term monitoring would support verification of sustained implementation.",

        "ai_summary": f"FALLBACK Earth observation analysis for {practice_name} on field '{field_name}' processed {total_scenes} satellite scenes. Data {'sourced from operational satellite systems (USGS M2M API, Microsoft Planetary Computer)' if using_real_data else 'generated from typical observation patterns'} provides supporting context for conservation verification. {'Note: AI summarization service temporarily unavailable - automated summary generation pending.' if error_msg else 'Manual review recommended for detailed interpretation.'}"
    }


def generate_field_overview(field, all_practices_data):
    """
    Generate overview summary for all practices on a field

    Args:
        field: Field model instance
        all_practices_data: List of dicts containing practice information

    Returns:
        String with overview summary
    """

    # Get API credentials
    api_key = settings.OPENAI_API_KEY
    base_url = settings.OPENAI_BASE_URL

    print(f"\n=== Field Overview Generation ===")
    print(f"Field: {field.field_name}")
    print(f"Practices: {len(all_practices_data)}")
    print(f"================================\n")

    prompt = f"""Provide a brief overview of conservation practices on this field:

Field: {field.field_name}
Area: {field.area_acres if field.area_acres else 'Unknown'} acres
Location: {field.county}, {field.state}

Practices implemented:
{json.dumps(all_practices_data, indent=2)}

Write a 3-4 sentence overview summarizing the conservation efforts on this field over time.
Focus on observable patterns and practice continuity. Do not make compliance judgments."""

    try:
        print("Creating OpenAI client for field overview...")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        print("Sending field overview request to OpenAI API...")
        response = client.chat.completions.create(
            model="claude-4-sonnet",
            messages=[
                {
                    "role": "system",
                    "content": "You are a conservation data analyst writing neutral observational summaries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        overview = response.choices[0].message.content
        print(f"Field overview generated: {overview[:100]}...")
        return overview

    except Exception as e:
        error_msg = str(e)
        print(f"Field overview generation failed: {error_msg}")

        # Return a simple fallback based on data
        practice_list = ", ".join([p.get('practice', 'Unknown') for p in all_practices_data])
        years = [p.get('year', 'N/A') for p in all_practices_data]
        year_range = f"{min(years)}-{max(years)}" if years and len(years) > 1 else str(years[0]) if years else 'N/A'

        return f"Field '{field.field_name}' ({field.area_acres if field.area_acres else 'Unknown'} acres) in {field.county}, {field.state} has {len(all_practices_data)} conservation practice(s) implemented: {practice_list}. Practice implementation spans {year_range}. Earth observation data is available to support verification of these practices through multi-temporal satellite monitoring."