from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Literal
from app.diff_parser import GitHubClient, DiffParser
from app.agents import AgentOrchestrator


app = FastAPI(
    title="Github PR Review Agent",
    description="An AI agent that reviews GitHub pull requests and provides feedback.",
    version="1.0.0"
)

# Add CORS middleware for API calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic Models
class HealthCheck(BaseModel):
    status: str
    msg: str

class PRReviewRequest(BaseModel):
    github_url: HttpUrl

class DiffReviewRequest(BaseModel):
    diff_text: str

class Comment(BaseModel):
    file: str
    line: int
    severity: Literal["high", "medium", "low"]
    category: Literal["logic", "security", "performance", "readability"]
    message: str
    suggestion: str

class ReviewResponse(BaseModel):
    summary: dict
    comments: List[Comment]

# Initialize services
github_client = GitHubClient()
diff_parser = DiffParser()
orchestrator = AgentOrchestrator()

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/healthcheck", response_model=HealthCheck)
def healthcheck_endpoint():
    return HealthCheck(status="ok", msg="Service is up and running smoothly.")

@app.post("/review/pr", response_model=ReviewResponse)
async def review_pr(request: PRReviewRequest):
    try:
        # Fetch diff from GitHub
        diff_text = await github_client.fetch_pr_diff(str(request.github_url))
        
        # Parse diff
        parsed_diff = diff_parser.parse(diff_text)
        
        # Run multi-agent review
        comments = await orchestrator.review(parsed_diff)
        comments = [Comment(**c) for c in comments]
        
        # Generate summary
        summary = {
            "total_comments": len(comments),
            "high": sum(1 for c in comments if c.severity == "high"),
            "medium": sum(1 for c in comments if c.severity == "medium"),
            "low": sum(1 for c in comments if c.severity == "low")
        }
        
        return ReviewResponse(summary=summary, comments=comments)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/review/diff", response_model=ReviewResponse)
async def review_diff(request: DiffReviewRequest):
    try:
        # Parse diff
        parsed_diff = diff_parser.parse(request.diff_text)
        
        # Run multi-agent review
        comments = await orchestrator.review(parsed_diff)
        comments = [Comment(**c) for c in comments]

        # Generate summary
        summary = {
            "total_comments": len(comments),
            "high": sum(1 for c in comments if c.severity == "high"),
            "medium": sum(1 for c in comments if c.severity == "medium"),
            "low": sum(1 for c in comments if c.severity == "low")
        }

        return ReviewResponse(summary=summary, comments=comments)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))