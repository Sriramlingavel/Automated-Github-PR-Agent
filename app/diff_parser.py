import httpx
import re
from typing import Dict, List
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

@dataclass
class Change:
    type: str  # add/remove/context
    line_num: int
    content: str

@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    changes: List[Change]

@dataclass
class FileChange:
    path: str
    hunks: List[Hunk]

@dataclass
class ParsedDiff:
    files: List[FileChange]

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3.diff",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    async def fetch_pr_diff(self, pr_url: str) -> str:
        """Fetch diff from GitHub PR URL"""
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, pr_url)
        
        if not match:
            raise ValueError("Invalid GitHub PR URL")
        
        owner, repo, pr_number = match.groups()
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(api_url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.text

class DiffParser:
    def parse(self, diff_text: str) -> ParsedDiff:
        """Parse git diff format into structured data"""
        files = []
        current_file = None
        current_hunk = None
        new_line_num = 0
        
        lines = diff_text.split('\n')
        
        for line in lines:
            # New file
            if line.startswith('diff --git'):
                if current_file:
                    files.append(current_file)
                current_file = None
                current_hunk = None
            
            # File path
            elif line.startswith('+++'):
                path = line[6:].strip()
                if path != '/dev/null':
                    current_file = FileChange(path=path, hunks=[])
            
            # Hunk header
            elif line.startswith('@@'):
                if current_hunk and current_file:
                    current_file.hunks.append(current_hunk)
                
                # Parse @@ -10,5 +10,7 @@
                match = re.search(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
                if match:
                    old_start, old_count, new_start, new_count = map(int, match.groups())
                    current_hunk = Hunk(
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        changes=[]
                    )
                    new_line_num = new_start
            
            # Changes
            elif current_hunk and current_file:
                if line.startswith('+') and not line.startswith('+++'):
                    current_hunk.changes.append(Change(
                        type='add',
                        line_num=new_line_num,
                        content=line[1:]
                    ))
                    new_line_num += 1
                elif line.startswith('-') and not line.startswith('---'):
                    current_hunk.changes.append(Change(
                        type='remove',
                        line_num=new_line_num,
                        content=line[1:]
                    ))
                elif line.startswith(' '):
                    current_hunk.changes.append(Change(
                        type='context',
                        line_num=new_line_num,
                        content=line[1:]
                    ))
                    new_line_num += 1
        
        # Add last file
        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            files.append(current_file)
        
        return ParsedDiff(files=files)
    
if __name__ == "__main__":
    async def main():
        # Use a real public PR URL here
        pr_url = "https://github.com/tiangolo/fastapi/pull/10000"  
        # pr_url = "https://github.com/Sriramlingavel/DRL_Project/pull/1"
        #diff_text = "diff --git a/app/auth.py b/app/auth.py\nindex abc123..def456 100644\n--- a/app/auth.py\n+++ b/app/auth.py\n@@ -10,5 +10,7 @@ def login():\n def login():\n     username = input(\"Enter username\")\n-    password = input(\"Enter password\")\n+    password = getpass(\"Enter password\")\n+    if password == \"\":\n+        print(\"Empty password\")"
        
        print("\n--- FETCHING FROM GITHUB ---")
        client = GitHubClient()
        diff_text = await client.fetch_pr_diff(pr_url)

        print("\n--- RAW DIFF (FIRST 1500 CHARS) ---")
        print(diff_text[:1500])  

        print("\n--- PARSING DIFF ---")
        parser = DiffParser()
        parsed = parser.parse(diff_text)

        print("\n--- PARSED OUTPUT ---")
        for file in parsed.files[:3]:  # limit to first 3 files
            print(f"\nFile: {file.path}")
            for hunk in file.hunks[:2]:  # limit to first 2 hunks
                print(f"  Hunk: -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count}")
                for change in hunk.changes[:5]:  # limit lines
                    print(f"    [{change.type}] line {change.line_num}: {change.content}")

    asyncio.run(main())