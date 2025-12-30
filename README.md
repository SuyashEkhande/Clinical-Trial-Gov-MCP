<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastMCP-2.0+-00D4AA?style=for-the-badge" alt="FastMCP">
  <img src="https://img.shields.io/badge/Transport-Streamable_HTTP-FF6B6B?style=for-the-badge" alt="Streamable HTTP">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">🏥 ClinicalTrials.gov MCP Server</h1>

<p align="center">
  <strong>A semantic intelligence layer for clinical trial data</strong><br>
  Transform how AI agents interact with 400,000+ clinical trials
</p>

<p align="center">
  <strong>Built with ❤️ by <a href="https://in.linkedin.com/in/suyashekhande">Suyash Ekhande</a> for the clinical trials research community</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-tools">Tools</a> •
  <a href="#-examples">Examples</a> •
  <a href="#%EF%B8%8F-architecture">Architecture</a>
</p>

---



https://github.com/user-attachments/assets/87839f47-84fd-44ac-b1e5-4438cea40f92



## 🎯 What is this?

This is a **Model Context Protocol (MCP)** server that provides AI agents with intelligent, semantic access to [ClinicalTrials.gov](https://clinicaltrials.gov) — the world's largest database of clinical studies.

Unlike simple API wrappers, this server provides **10 high-level semantic tools** that understand clinical research workflows:

| Instead of... | You get... |
|--------------|------------|
| Raw API calls | Natural language queries like *"lung cancer trials with immunotherapy in Phase 3"* |
| Manual pagination | Automatic aggregation across thousands of results |
| Raw JSON responses | Computed metrics: trial maturity, enrollment pace, completion likelihood |
| Building queries | Automatic translation to the complex Essie query syntax |

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔍 Intelligent Search
- Natural language query support
- Auto-translation to Essie syntax
- 20+ filter parameters
- Proximity-based location search

### 🎯 Patient Matching
- Eligibility scoring (0-100)
- Age/gender/condition matching
- Detailed explanations
- Next steps guidance

### 📊 Computed Metrics
- Trial maturity assessment
- Enrollment pace analysis
- Completion likelihood
- Market saturation scores

</td>
<td width="50%">

### 🏢 Competitive Intelligence
- Similar trial discovery
- Sponsor pipeline analysis
- Therapeutic area mapping
- Collaboration networks

### 📈 Analytics
- Enrollment capacity analysis
- Geographic distribution
- Disease landscape trends
- Field value statistics

### 📤 Export & Format
- JSON, CSV, Markdown output
- Grouping strategies
- Summary statistics
- Batch processing

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip or any Python package manager

### Installation

#### Option 1: pip (recommended for development)

```bash
# Clone the repository
git clone https://github.com/yourusername/clinicaltrials-mcp.git
cd clinicaltrials-mcp

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

#### Option 2: Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/clinicaltrials-mcp.git
cd clinicaltrials-mcp

# Build the image
docker build -t clinicaltrials-mcp .

# Run the container
docker run -p 8000:8000 clinicaltrials-mcp
```

### Run the Server

```bash
# Start the MCP server (HTTP transport on port 8000)
python server.py
```

```
╭──────────────────────────────╮
│     FastMCP 2.14.1           │
│                              │
│  🖥  Server: clinicaltrials  │
│  📦 Transport: HTTP          │
│  🔗 URL: http://0.0.0.0:8000 │
╰──────────────────────────────╯
```

### Connect with any Agentic IDE/CLI


```json
{
  "mcpServers": {
    "clinicaltrials": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## 🛠 Tools

### Core Tools

| Tool | Description |
|------|-------------|
| **`search_clinical_trials`** | Natural language trial discovery with comprehensive filtering. Supports queries like *"diabetes AND metformin in phase 3 recruiting in California"* |
| **`analyze_trial_details`** | Deep-dive analysis with eligibility parsing, arm/intervention mapping, outcomes, and computed metrics |
| **`match_patient_to_trials`** | Patient-centric matching with eligibility scoring, explanations, and actionable next steps |
| **`get_trial_metadata_schema`** | Self-documenting API introspection — discover available fields, enums, and query syntax |

### Analysis Tools

| Tool | Description |
|------|-------------|
| **`find_similar_trials`** | Competitive landscape analysis with similarity scoring across conditions, interventions, and phases |
| **`analyze_trial_outcomes`** | Extract and compare primary/secondary outcome measures across trials |
| **`get_enrollment_intelligence`** | Market capacity analysis with enrollment patterns, saturation scores, and velocity insights |

### Intelligence Tools

| Tool | Description |
|------|-------------|
| **`analyze_sponsor_network`** | Organization portfolio analysis with therapeutic focus, pipeline stage distribution, and collaborations |
| **`export_and_format_trials`** | Batch export in JSON, CSV, or Markdown with grouping and summary statistics |
| **`query_trial_statistics`** | Aggregate analytics: geographic distribution, disease landscape, enrollment patterns |

---

## 💬 Examples

### Patient Trial Matching

> *"I'm a 55-year-old male with Type 2 Diabetes in California. What clinical trials can I join?"*

```python
result = await match_patient_to_trials(
    age=55,
    gender="MALE",
    primary_condition="Type 2 Diabetes",
    location_state="California",
    must_be_recruiting=True
)
# Returns: Matched trials with eligibility scores and explanations
```

### Competitive Intelligence

> *"Find all Phase 3 NSCLC trials with checkpoint inhibitors and analyze the competitive landscape"*

```python
# Search for trials
trials = await search_clinical_trials(
    query="NSCLC AND checkpoint inhibitor",
    trial_phase=["PHASE3"],
    enrollment_status=["RECRUITING"]
)

# Analyze similar trials for a reference
similar = await find_similar_trials(
    reference_nct_id="NCT04000165",
    similarity_dimensions=["CONDITION", "INTERVENTION", "PHASE"]
)
```

### Sponsor Analysis

> *"Analyze Pfizer's oncology pipeline — what are their active trials and therapeutic focus areas?"*

```python
result = await analyze_sponsor_network(
    sponsor_name="Pfizer",
    analyze_therapeutic_areas=True,
    analyze_stage_distribution=True,
    analyze_collaboration_patterns=True
)
# Returns: Portfolio breakdown, phase distribution, top conditions, collaborators
```

### Market Analysis

> *"What's the enrollment situation for melanoma trials in the United States?"*

```python
result = await get_enrollment_intelligence(
    condition="melanoma",
    location_country="United States",
    include_capacity_analysis=True,
    include_competitor_summary=True
)
# Returns: Market saturation, enrollment targets, top sponsors, recommendations
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Clients                               │
│              (Claude Desktop, AI Agents, etc.)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Streamable HTTP (port 8000)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastMCP Server                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    10 Semantic Tools                      │   │
│  │  search | analyze | match | metadata | similar | outcomes │   │
│  │  enrollment | sponsor | export | statistics               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   Essie     │  │   Pagination    │  │    Metrics      │     │
│  │ Translator  │  │    Handler      │  │   Calculator    │     │
│  └─────────────┘  └─────────────────┘  └─────────────────┘     │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Async HTTP Client (aiohttp)                  │   │
│  │         TTL Caching | Retry Logic | Error Handling        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                ClinicalTrials.gov API v2                         │
│                    400,000+ Studies                              │
└─────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
clinicaltrials-gov-mcp/
├── server.py              # FastMCP server with 10 tools
├── config.py              # API settings, cache TTLs, field lists
├── core/
│   ├── api_client.py      # Async HTTP client with caching & retry
│   ├── models.py          # Pydantic schemas (28 enums, 15 models)
│   ├── pagination.py      # Token-based pagination handler
│   └── essie_translator.py # Natural language → Essie query syntax
├── tools/
│   ├── search.py          # Trial search with NL support
│   ├── analyze.py         # Trial analysis & similarity
│   ├── patient_match.py   # Patient eligibility matching
│   ├── metadata.py        # API schema introspection
│   ├── enrollment.py      # Enrollment intelligence
│   ├── sponsor.py         # Sponsor network analysis
│   ├── export.py          # Multi-format export
│   └── statistics.py      # Aggregate analytics
└── utils/
    ├── metrics.py         # Computed metrics (maturity, pace, etc.)
    └── formatting.py      # Output formatting (Markdown, CSV)
```

---

## 🔧 Technical Details

### Key Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **HTTP Client** | aiohttp | httpx returned 403s from ClinicalTrials.gov; aiohttp works reliably |
| **Caching** | TTLCache (cachetools) | Separate caches for metadata (24h), statistics (6h), studies (1h), searches (15min) |
| **Query Translation** | Rules-based Essie translator | Converts natural language to ClinicalTrials.gov's complex query syntax |
| **Pagination** | Token-based with streaming | Handles large result sets efficiently with optional streaming |
| **Transport** | Streamable HTTP | Modern MCP transport for production deployments |

### Essie Query Syntax

The server automatically translates natural language queries:

```
Input:  "lung cancer AND pembrolizumab in phase 3"
Output: AREA[Condition]"lung cancer" AND AREA[InterventionName]pembrolizumab AND AREA[Phase]PHASE3

Input:  "recruiting diabetes trials in California"
Output: AREA[Condition]diabetes AND AREA[OverallStatus]RECRUITING AND AREA[LocationState]"California"
```

### Computed Metrics

| Metric | Calculation |
|--------|-------------|
| **Trial Maturity** | Based on phase, status, and time since start (EARLY/MID/LATE) |
| **Enrollment Pace** | Expected vs actual timeline based on phase benchmarks |
| **Completion Likelihood** | Statistical likelihood based on phase and sponsor class |
| **Similarity Score** | Weighted matching across conditions, interventions, phase, and sponsor |

---

## 🧪 Testing

```bash
# Run the test suite
python test_tools.py
```

This tests all 10 tools against the live API:

```
1️⃣  search_clinical_trials     ✅ SUCCESS
2️⃣  analyze_trial_details      ✅ SUCCESS
3️⃣  match_patient_to_trials    ✅ SUCCESS
4️⃣  get_trial_metadata_schema  ✅ SUCCESS
5️⃣  find_similar_trials        ✅ SUCCESS
6️⃣  analyze_trial_outcomes     ✅ SUCCESS
7️⃣  get_enrollment_intelligence ✅ SUCCESS
8️⃣  analyze_sponsor_network    ✅ SUCCESS
9️⃣  export_and_format_trials   ✅ SUCCESS
🔟 query_trial_statistics      ✅ SUCCESS
```

---

## 📚 API Reference

This server interfaces with the [ClinicalTrials.gov REST API v2](https://clinicaltrials.gov/data-api/api).

### Endpoints Used
- `GET /studies` — Search and filter studies
- `GET /studies/{nctId}` — Retrieve single study details
- `GET /studies/metadata` — Data model schema
- `GET /studies/enums` — Enumeration values
- `GET /studies/search-areas` — Searchable fields
- `GET /stats/*` — Aggregate statistics
- `GET /version` — API version

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## Acknowledgments

- [ClinicalTrials.gov](https://clinicaltrials.gov) for providing the public API
- [FastMCP](https://gofastmcp.com) for the excellent MCP framework
- [Model Context Protocol](https://modelcontextprotocol.io) for the specification

---

<p align="center">
  <strong>Built with ❤️ by <a href="https://in.linkedin.com/in/suyashekhande">Suyash Ekhande</a> for the clinical trials research community</strong>
</p>
