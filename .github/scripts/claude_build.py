import os
from anthropic import Anthropic

task = os.environ["TASK"]

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

prompt = f"""
You are a careful software documentation assistant.
Your job is to update README.md based on the user's task.

Rules:
- Return only the full updated README.md content.
- Do not wrap it in markdown fences.
- Keep the existing title.
- Make the README clear and useful.
- Do not invent complex setup steps. If details are unknown, use sensible placeholder guidance.

User task:
{task}

Current README.md:
{readme}
"""

message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=2000,
    messages=[
        {"role": "user", "content": prompt}
    ],
)

updated_readme = message.content[0].text

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated_readme)
