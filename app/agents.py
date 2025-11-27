import asyncio
import json
import os
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.diff_parser import DiffParser, ParsedDiff
from dotenv import load_dotenv

load_dotenv()

class Comment:
    def __init__(self, file: str, line: int, severity: str, category: str, message: str, suggestion: str):
        self.file = file
        self.line = line
        self.severity = severity
        self.category = category
        self.message = message
        self.suggestion = suggestion

class BaseAgent:
    def __init__(self, category: str, prompt_template: str):
        self.category = category
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1
        )
        self.prompt = PromptTemplate(
            input_variables=["diff_context"],
            template=prompt_template
        )
        self.parser = JsonOutputParser()
    
    def _format_diff(self, parsed_diff: ParsedDiff) -> str:
        """Convert ParsedDiff to readable string"""
        output = []
        for file in parsed_diff.files:
            output.append(f"\n=== File: {file.path} ===")
            for hunk in file.hunks:
                output.append(f"@@ Lines {hunk.new_start}-{hunk.new_start + hunk.new_count} @@")
                for change in hunk.changes:
                    if change.type == 'add':
                        output.append(f"+ Line {change.line_num}: {change.content}")
                    elif change.type == 'remove':
                        output.append(f"- Line {change.line_num}: {change.content}")
        return "\n".join(output)
    
    async def analyze(self, parsed_diff: ParsedDiff) -> List[Comment]:
        """Analyze diff and return comments"""
        diff_context = self._format_diff(parsed_diff)
        
        prompt_text = self.prompt.format(diff_context=diff_context)
        
        try:
            response = await self.llm.ainvoke(prompt_text)
            
            # Extract JSON from response
            content = response.content
            
            # Clean markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            comments_data = json.loads(content.strip())
            
            # Convert to Comment objects
            comments = []
            for c in comments_data:
                comments.append(Comment(
                    file=c.get("file", "unknown"),
                    line=c.get("line", 0),
                    severity=c.get("severity", "low"),
                    category=self.category,
                    message=c.get("message", ""),
                    suggestion=c.get("suggestion", "")
                ))
            
            return comments
        
        except Exception as e:
            print(f"Error in {self.category} agent: {e}")
            return []

class AgentOrchestrator:
    def __init__(self):
        # Load prompts
        with open("app/prompts.json", "r") as f:
            prompts = json.load(f)
        
        self.agents = {
            "logic": BaseAgent("logic", prompts["logic"]),
            "security": BaseAgent("security", prompts["security"]),
            "performance": BaseAgent("performance", prompts["performance"]),
            "readability": BaseAgent("readability", prompts["readability"])
        }
    
    async def review(self, parsed_diff: ParsedDiff) -> List[Dict]:
        """Run all agents in parallel and aggregate results"""
        tasks = [agent.analyze(parsed_diff) for agent in self.agents.values()]
        results = await asyncio.gather(*tasks)
        
        # Flatten and deduplicate
        all_comments = []
        seen = set()
        
        for agent_comments in results:
            for comment in agent_comments:
                key = f"{comment.file}:{comment.line}:{comment.message[:50]}"
                if key not in seen:
                    seen.add(key)
                    all_comments.append({
                        "file": comment.file,
                        "line": comment.line,
                        "severity": comment.severity,
                        "category": comment.category,
                        "message": comment.message,
                        "suggestion": comment.suggestion
                    })
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        all_comments.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return all_comments
    
if __name__ == "__main__":

    async def main():
        # Fake diff for testing
        test_diff = """diff --git a/app/auth.py b/app/auth.py
index abc123..def456 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -10,5 +10,7 @@ def login():
 def login():
     username = input("Enter username")
-    password = input("Enter password")
+    password = getpass("Enter password")
+    if password == "":
+        print("Empty password")
"""

        print("\n--- Parsing Diff ---")
        parser = DiffParser()
        parsed = parser.parse(test_diff)

        print("\n--- Running Agents ---")
        orchestrator = AgentOrchestrator()
        results = await orchestrator.review(parsed)

        print("\n--- FINAL REVIEW COMMENTS ---")
        for r in results:
            print("\n----------------")
            print(f"File: {r['file']}")
            print(f"Line: {r['line']}")
            print(f"Severity: {r['severity']}")
            print(f"Category: {r['category']}")
            print(f"Message: {r['message']}")
            print(f"Suggestion: {r['suggestion']}")

    asyncio.run(main())
