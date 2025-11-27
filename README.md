# Automated GitHub PR Review Agent

An AI-powered code review system that analyzes GitHub Pull Requests using a multi-agent architecture. The system provides structured feedback across four key dimensions: logic, security, performance, and readability.

## Live Demo

Frontend: https://automated-github-pr-agent.onrender.com/

API Documentation: https://automated-github-pr-agent.onrender.com/docs

---

## Features

- Multi-agent analysis using specialized AI agents
- Parallel processing for faster reviews
- Direct GitHub PR integration via URL
- Support for raw git diff input
- REST API for programmatic access
- Web interface for manual reviews

---

## Architecture

The system follows a pipeline architecture:

1. **Input Layer**: Accepts GitHub PR URLs or raw git diffs
2. **Parsing Layer**: Extracts structured data from git diff format
3. **Analysis Layer**: Four specialized agents analyze code in parallel
4. **Aggregation Layer**: Merges, deduplicates, and ranks findings
5. **Output Layer**: Returns structured JSON with severity-ranked comments

Each agent focuses on a specific concern:
- Logic Agent: Bugs, edge cases, type errors
- Security Agent: Vulnerabilities, authentication issues, input validation
- Performance Agent: Inefficient operations, database queries, algorithms
- Readability Agent: Code quality, naming conventions, maintainability

---

## Repository Structure

```
AUTOMATES-GITHUB-PR-AGENT/
├── app/
│   ├── __init__.py           
│   ├── main.py               
│   ├── agents.py             
│   ├── diff_parser.py        
│   └── prompts.json          
├── static/
│   └── index.html            
├── .env                      
├── requirements.txt          
└── README.md                 
```

---

## File Descriptions

### app/main.py
FastAPI application containing all API endpoints and routing logic. Includes Pydantic models for request/response validation, CORS middleware for frontend communication, and static file serving for the web interface.

Key endpoints:
- `POST /review/pr` - Analyze GitHub PR by URL
- `POST /review/diff` - Analyze raw git diff
- `GET /healthcheck` - Service status
- `GET /` - Web interface

### app/agents.py
Multi-agent orchestration system built with Langchain and Google Gemini.

**BaseAgent**: Core agent class that initializes the LLM, formats diff context, and parses structured JSON responses.

**AgentOrchestrator**: Coordinates all agents, runs them concurrently using asyncio, deduplicates similar findings, and ranks results by severity.

### app/diff_parser.py
Git diff parsing and GitHub API integration.

**GitHubClient**: Handles GitHub API requests. Extracts repository information from PR URLs and fetches raw diff content. Supports optional authentication for private repositories.

**DiffParser**: Converts git diff text into structured data objects. Parses file paths, hunk headers, and individual line changes into Python dataclasses.

### app/prompts.json
Prompt templates for each specialized agent. Separated from code to allow independent iteration on prompt engineering without modifying application logic.

### static/index.html
Single-page web interface. Provides tabbed input for PR URLs and raw diffs, real-time analysis feedback, and formatted display of results with severity-based color coding.

### app/__init__.py
Python package marker file. Required for Python to treat the app directory as an importable package.

---

## Quick Setup

### Prerequisites
- Python 3.9 or higher
- Google AI API Key (obtain from https://makersuite.google.com/app/apikey)
- GitHub Personal Access Token (optional, for private repositories)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/automates-github-pr-agent.git
cd automates-github-pr-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cat > .env << EOF
GOOGLE_API_KEY=your_google_api_key_here
GITHUB_TOKEN=your_github_token_here
EOF

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points

- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/healthcheck

---

## API Usage

### Review GitHub PR

```bash
POST /review/pr
Content-Type: application/json

{
  "github_url": "https://github.com/owner/repo/pull/123"
}
```

### Review Raw Diff

```bash
POST /review/diff
Content-Type: application/json

{
  "diff_text": "diff --git a/file.py b/file.py\n..."
}
```

### Response Format

```json
{
  "summary": {
    "total_comments": 5,
    "high": 2,
    "medium": 2,
    "low": 1
  },
  "comments": [
    {
      "file": "src/auth.py",
      "line": 42,
      "severity": "high",
      "category": "security",
      "message": "Hardcoded API key detected",
      "suggestion": "Move to environment variables"
    }
  ]
}
```

---

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **LLM**: Google Gemini 2.0 Flash
- **Orchestration**: Langchain
- **Async Processing**: asyncio
- **HTTP Client**: httpx
- **Validation**: Pydantic
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Render

---

## Configuration

### Environment Variables

| Variable | Necessary | Purpose |
|----------|----------|---------|
| GOOGLE_API_KEY | Yes | Google AI API authentication |
| GITHUB_TOKEN | No | GitHub API rate limit increase |

### Customizing Agent Prompts

Edit `app/prompts.json` to modify agent behavior. Each agent has a dedicated prompt that defines its analysis focus and output format.

---

## Deployment

### Render Deployment

1. Push code to GitHub repository
2. Create new Web Service on render.com
3. Connect GitHub repository
4. Configure build and start commands:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard
6. Deploy

### Railway Deployment

1. Push code to GitHub
2. Create new project on railway.app
3. Connect repository
4. Add environment variables
5. Railway automatically detects and deploys FastAPI application

---

## Troubleshooting


### Google API Rate Limit (429 Error)

Check quota at Google AI Studio. Free tier has daily limits. Consider upgrading or waiting for quota reset.

### GitHub Rate Limit (403 Error)

Add GITHUB_TOKEN to .env file. This increases rate limit from 60 to 5,000 requests per hour.

---
## License

MIT License

---
