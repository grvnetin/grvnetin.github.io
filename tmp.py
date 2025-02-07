import requests
import json
import re
import os

# Jira API Configuration
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://your-jira-instance.atlassian.net")
PROJECT_KEY = os.getenv("PROJECT_KEY", "PROJ")
RELEASE_VERSION_PATTERN = os.getenv("RELEASE_VERSION_PATTERN", r"\d{4}_Sprint\d+")
AUTH = (os.getenv("JIRA_EMAIL", "your-email@example.com"), os.getenv("JIRA_API_TOKEN", "your-api-token"))

# Fetch release issues from Jira API
def get_release_issues():
    url = f"{JIRA_BASE_URL}/rest/api/2/search"
    query = {
        "jql": f'project="{PROJECT_KEY}" ORDER BY priority DESC',
        "maxResults": 100,
        "fields": [
            "key", "summary", "issuetype", "priority", "status", "assignee",
            "reporter", "labels", "components", "created", "updated",
            "resolution", "timeoriginalestimate", "timespent", "fixVersions",
            "customfield_impact", "customfield_customerImpact", "customfield_releaseStrategy"
        ]
    }

    try:
        if isinstance(AUTH, tuple):
            response = requests.get(url, params={"jql": query["jql"], "maxResults": query["maxResults"]}, auth=AUTH)
        else:
            headers = {"Authorization": f"Bearer {AUTH}"}
            response = requests.get(url, params={"jql": query["jql"], "maxResults": query["maxResults"]}, headers=headers)
        
        response.raise_for_status()
        issues = response.json().get("issues", [])
        # Filter issues based on the release version pattern
        filtered_issues = [issue for issue in issues if any(re.match(RELEASE_VERSION_PATTERN, fv['name']) for fv in issue['fields'].get('fixVersions', []))]
        return filtered_issues
    except requests.exceptions.RequestException as e:
        print(f"Error fetching issues: {e}")
        return []

# Extract release version from issues
def extract_release_version(issues):
    for issue in issues:
        for fix_version in issue['fields'].get('fixVersions', []):
            if re.match(RELEASE_VERSION_PATTERN, fix_version['name']):
                return fix_version['name']
    return "unknown_release"

# Generate Markdown content
def generate_markdown(issues, release_version):
    markdown_content = f"# Jira Release Report: {release_version}\n\n"
    markdown_content += f"**Project:** {PROJECT_KEY}\n"
    markdown_content += f"**Total Issues:** {len(issues)}\n\n"
    markdown_content += "---\n\n"
    markdown_content += "## Table of Contents\n"
    for issue in issues:
        markdown_content += f"- [{issue['key']}: {issue['fields'].get('summary', 'No Summary')}](#{issue['key'].lower()})\n"
    markdown_content += "\n---\n"

    for issue in issues:
        fields = issue.get("fields", {})
        markdown_content += f"## {issue['key']}: {fields.get('summary', 'No Summary')}\n"
        markdown_content += f"- **Type:** {fields.get('issuetype', {}).get('name', 'N/A')}\n"
        markdown_content += f"- **Priority:** {fields.get('priority', {}).get('name', 'N/A')}\n"
        markdown_content += f"- **Status:** {fields.get('status', {}).get('name', 'N/A')}\n"
        markdown_content += f"- **Assignee:** {fields.get('assignee', {}).get('displayName', 'Unassigned')}\n"
        markdown_content += f"- **Reporter:** {fields.get('reporter', {}).get('displayName', 'N/A')}\n"
        markdown_content += f"- **Created:** {fields.get('created', 'N/A')}\n"
        markdown_content += f"- **Updated:** {fields.get('updated', 'N/A')}\n"
        markdown_content += f"- **Labels:** {', '.join(fields.get('labels', [])) or 'None'}\n"
        markdown_content += f"- **Components:** {', '.join([comp['name'] for comp in fields.get('components', [])]) or 'None'}\n"
        markdown_content += f"- **Estimated Time:** {fields.get('timeoriginalestimate', 'N/A')} seconds\n"
        markdown_content += f"- **Time Spent:** {fields.get('timespent', 'N/A')} seconds\n"
        markdown_content += f"- **Business Impact:** {fields.get('customfield_impact', 'N/A')}\n"
        markdown_content += f"- **Customer Impact:** {fields.get('customfield_customerImpact', 'N/A')}\n"
        markdown_content += f"- **Release Strategy:** {fields.get('customfield_releaseStrategy', 'N/A')}\n"
        markdown_content += "---\n"

    return markdown_content

# Save Markdown file
def save_markdown(content, release_version):
    file_name = f"jira_release_report_{release_version}.md"
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Markdown report saved: {file_name}")

# Save release version to a file
def save_release_version(release_version):
    with open("release_version.txt", "w") as file:
        file.write(release_version)

# Fetch data and create markdown
issues = get_release_issues()
if issues:
    release_version = extract_release_version(issues)
    save_release_version(release_version)
    markdown_content = generate_markdown(issues, release_version)
    save_markdown(markdown_content, release_version)
else:
    print("No issues found for this release.")
