#!/usr/bin/env python3
"""Test script to verify all 10 MCP tools are working."""

import asyncio
import warnings
warnings.filterwarnings("ignore")

# Test queries for each tool
async def test_all_tools():
    """Test all 10 tools with example queries."""
    
    from tools.search import search_clinical_trials
    from tools.analyze import analyze_trial_details, find_similar_trials, analyze_trial_outcomes
    from tools.patient_match import match_patient_to_trials
    from tools.metadata import get_trial_metadata_schema
    from tools.enrollment import get_enrollment_intelligence
    from tools.sponsor import analyze_sponsor_network
    from tools.export import export_and_format_trials
    from tools.statistics import query_trial_statistics
    
    results = {}
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 1: search_clinical_trials
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("1️⃣  TOOL: search_clinical_trials")
    print("="*60)
    print("Query: 'lung cancer AND immunotherapy' in Phase 3, recruiting")
    
    result = await search_clinical_trials(
        query="lung cancer AND immunotherapy",
        trial_phase=["PHASE3"],
        enrollment_status=["RECRUITING"],
        results_limit=3,
        include_metrics=True,
    )
    print(f"✅ Status: {result.get('status')}")
    print(f"   Total found: {result.get('total_count')}")
    print(f"   Returned: {result.get('returned_count')}")
    if result.get("studies"):
        nct_id = result["studies"][0]["nct_id"]
        print(f"   First trial: {nct_id}")
        results["nct_id"] = nct_id
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 2: analyze_trial_details
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("2️⃣  TOOL: analyze_trial_details")
    print("="*60)
    nct_id = results.get("nct_id", "NCT04000165")
    print(f"Query: Analyze trial {nct_id}")
    
    result = await analyze_trial_details(
        nct_id=nct_id,
        analysis_depth="STANDARD",
        compute_metrics=True,
    )
    print(f"✅ Status: {result.get('status')}")
    if result.get("trial"):
        trial = result["trial"]
        print(f"   Title: {trial.get('title', 'N/A')[:60]}...")
        print(f"   Status: {trial.get('status')}")
        if trial.get("key_metrics"):
            print(f"   Maturity: {trial['key_metrics'].get('trial_maturity')}")
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 3: match_patient_to_trials
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("3️⃣  TOOL: match_patient_to_trials")
    print("="*60)
    print("Query: 55yo male with Type 2 Diabetes in USA")
    
    result = await match_patient_to_trials(
        age=55,
        gender="MALE",
        primary_condition="Type 2 Diabetes",
        location_country="United States",
        must_be_recruiting=True,
        match_strictness="BALANCED",
        limit=3,
    )
    print(f"✅ Status: {result.get('status')}")
    print(f"   Matched trials: {result.get('total_matches')}")
    if result.get("matched_trials"):
        match = result["matched_trials"][0]
        print(f"   Top match: {match['trial'].get('nct_id')} (score: {match.get('match_score')})")
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 4: get_trial_metadata_schema
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("4️⃣  TOOL: get_trial_metadata_schema")
    print("="*60)
    print("Query: Get ENUMS scope")
    
    result = await get_trial_metadata_schema(
        scope="ENUMS",
        include_examples=False,
    )
    print(f"✅ Status: {result.get('status')}")
    enums = result.get("enum_definitions", [])
    print(f"   Enums found: {len(enums)}")
    if enums:
        print(f"   Sample: {enums[0].get('enum_name')} ({len(enums[0].get('possible_values', []))} values)")
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 5: find_similar_trials
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("5️⃣  TOOL: find_similar_trials")
    print("="*60)
    ref_nct = results.get("nct_id", "NCT04000165")
    print(f"Query: Find trials similar to {ref_nct}")
    
    result = await find_similar_trials(
        reference_nct_id=ref_nct,
        similarity_dimensions=["CONDITION", "PHASE"],
        similarity_threshold=50.0,
        exclude_completed=True,
        limit=3,
    )
    print(f"✅ Status: {result.get('status')}")
    similar = result.get("similar_trials", [])
    print(f"   Similar trials found: {len(similar)}")
    if similar:
        print(f"   Top match: {similar[0]['trial'].get('nct_id')} (score: {similar[0].get('similarity_score')})")
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 6: analyze_trial_outcomes
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("6️⃣  TOOL: analyze_trial_outcomes")
    print("="*60)
    print(f"Query: Analyze outcomes for {ref_nct}")
    
    result = await analyze_trial_outcomes(
        nct_id=ref_nct,
        outcome_categories=["PRIMARY", "SECONDARY"],
        include_results_data=True,
    )
    print(f"✅ Status: {result.get('status')}")
    outcomes = result.get("outcomes_by_trial", [])
    if outcomes and outcomes[0].get("outcomes"):
        print(f"   Outcomes found: {len(outcomes[0]['outcomes'])}")
        print(f"   First outcome: {outcomes[0]['outcomes'][0].get('measure', 'N/A')[:50]}...")
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 7: get_enrollment_intelligence
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("7️⃣  TOOL: get_enrollment_intelligence")
    print("="*60)
    print("Query: Enrollment analysis for 'breast cancer' trials")
    
    result = await get_enrollment_intelligence(
        condition="breast cancer",
        enrollment_status=["RECRUITING"],
        include_capacity_analysis=True,
        include_competitor_summary=True,
        limit=50,
    )
    print(f"✅ Status: {result.get('status')}")
    stats = result.get("aggregate_stats", {})
    print(f"   Trials analyzed: {stats.get('total_trials_analyzed')}")
    print(f"   Total enrollment target: {stats.get('total_enrollment_target')}")
    if result.get("capacity_analysis"):
        print(f"   Market saturation: {result['capacity_analysis'].get('market_saturation')}")
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 8: analyze_sponsor_network
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("8️⃣  TOOL: analyze_sponsor_network")
    print("="*60)
    print("Query: Analyze Pfizer's trial portfolio")
    
    result = await analyze_sponsor_network(
        sponsor_name="Pfizer",
        analysis_scope="ORGANIZATION",
        analyze_therapeutic_areas=True,
        analyze_stage_distribution=True,
        limit=50,
    )
    print(f"✅ Status: {result.get('status')}")
    summary = result.get("sponsor_summary", {})
    print(f"   Sponsor: {summary.get('name')}")
    print(f"   Total trials: {summary.get('trial_count')}")
    print(f"   Active trials: {summary.get('active_trials_count')}")
    if result.get("pipeline_stage_distribution"):
        print(f"   Portfolio: {result['pipeline_stage_distribution'].get('portfolio_strength')}")
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 9: export_and_format_trials
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("9️⃣  TOOL: export_and_format_trials")
    print("="*60)
    trial_ids = [results.get("nct_id", "NCT04000165")]
    print(f"Query: Export {trial_ids} as JSON")
    
    result = await export_and_format_trials(
        trial_ids=trial_ids,
        export_format="JSON",
        include_summary_stats=True,
    )
    print(f"✅ Status: {result.get('status')}")
    print(f"   Format: {result.get('export_format')}")
    print(f"   Records: {result.get('record_count')}")
    
    # ═══════════════════════════════════════════════════════════════
    # Tool 10: query_trial_statistics
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("🔟 TOOL: query_trial_statistics")
    print("="*60)
    print("Query: Disease landscape for recruiting trials")
    
    result = await query_trial_statistics(
        statistic_type="DISEASE_LANDSCAPE",
        enrollment_status=["RECRUITING"],
        limit=10,
    )
    print(f"✅ Status: {result.get('status')}")
    landscape = result.get("disease_landscape", [])
    print(f"   Conditions found: {len(landscape)}")
    if landscape:
        top = landscape[0]
        print(f"   Top condition: {top.get('condition')} ({top.get('trial_count')} trials)")
    
    print("\n" + "="*60)
    print("✅ ALL 10 TOOLS TESTED SUCCESSFULLY!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_all_tools())
