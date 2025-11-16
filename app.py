import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from github import GithubIntegration
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# GitHub App Config
GITHUB_APP_ID = os.getenv('GITHUB_APP_ID')
INSTALLATION_ID = os.getenv('GITHUB_INSTALLATION_ID')
PRIVATE_KEY_PATH = os.getenv('GITHUB_PRIVATE_KEY_PATH')
REPO_NAME = os.getenv('GITHUB_REPO')


def get_github_installation_client():
    """Authenticate as the GitHub App installation."""
    from github import Github
    with open(PRIVATE_KEY_PATH, 'r') as f:
        private_key = f.read()

    integration = GithubIntegration(GITHUB_APP_ID, private_key)
    access_token = integration.get_access_token(INSTALLATION_ID).token
    return Github(access_token)


def create_pr_with_metadata(topic_name, partitions, description):
    """Create PR in GitHub repo with metadata.json for topic."""
    gh = get_github_installation_client()
    repo = gh.get_repo(REPO_NAME)

    branch_name = f"request/{topic_name}"
    base_branch = repo.get_branch('main')

    # Create new branch from main
    repo.create_git_ref(ref=f'refs/heads/{branch_name}', sha=base_branch.commit.sha)

    # Create topic metadata
    metadata = {
        "resource_type": "topic",
        "topic_name": topic_name,
        "partitions": partitions,
        "description": description
    }

    # Save metadata to JSON string
    content = json.dumps(metadata, indent=2)
    file_path = f"requests/topics/{topic_name}/metadata.json"

    # Commit the file
    repo.create_file(
        path=file_path,
        message=f"Add metadata for topic {topic_name}",
        content=content,
        branch=branch_name
    )

    # Open PR
    pr = repo.create_pull(
        title=f"Request: Create topic {topic_name}",
        body=f"This PR contains metadata for topic `{topic_name}`.",
        head=branch_name,
        base='main'
    )

    return pr.html_url


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    topic_name = request.form.get('topic_name')
    partitions = request.form.get('partitions')
    description = request.form.get('description')

    if not topic_name or not partitions:
        flash("Topic name and partitions are required!", "danger")
        return redirect(url_for('index'))

    try:
        pr_url = create_pr_with_metadata(topic_name, partitions, description)
        flash(f"✅ Pull Request created successfully! <a href='{pr_url}' target='_blank'>View PR on GitHub 🚀</a>", "success")
        return redirect(url_for('index'))
    except Exception as e:
        print("Error creating PR:", e)
        flash(f"❌ Failed to create PR: {e}", "danger")
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
