"""
ARTHUR Git Projects Integration
Monitors local Git repositories and projects
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import git
from git import Repo, InvalidGitRepositoryError


class GitProjectsManager:
    """Manages and monitors local Git projects"""

    def __init__(self, project_paths: List[str] = None):
        """
        Initialize Git projects manager

        Args:
            project_paths: List of paths to scan for Git repos
        """
        self.project_paths = project_paths or []
        self.repos: Dict[str, Repo] = {}

        if not self.project_paths:
            self._auto_detect_paths()

        self._scan_repos()

    def _auto_detect_paths(self):
        """Auto-detect common project directories"""
        home = Path.home()
        common_paths = [
            home / "Documents" / "GitHub",
            home / "Documents" / "Projects",
            home / "Projects",
            home / "Development",
            home / "dev",
            home / "code",
            home / "repos",
            home / "GitHub",
        ]

        for path in common_paths:
            if path.exists():
                self.project_paths.append(str(path))

    def _scan_repos(self):
        """Scan project paths for Git repositories"""
        self.repos = {}

        for base_path in self.project_paths:
            base = Path(base_path)
            if not base.exists():
                continue

            if (base / ".git").exists():
                try:
                    self.repos[base.name] = Repo(base)
                except InvalidGitRepositoryError:
                    pass

            for item in base.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    try:
                        self.repos[item.name] = Repo(item)
                    except InvalidGitRepositoryError:
                        pass

    def add_project_path(self, path: str):
        """Add a project path and rescan"""
        if path not in self.project_paths:
            self.project_paths.append(path)
            self._scan_repos()

    def list_projects(self) -> str:
        """Get formatted list of all projects"""
        if not self.repos:
            return "No Git projects found. Add project paths in config."

        lines = [f"Git Projects ({len(self.repos)} found):"]

        for name, repo in sorted(self.repos.items()):
            try:
                branch = repo.active_branch.name
                status = self._get_status_indicator(repo)
                lines.append(f"  {status} {name} [{branch}]")
            except Exception as e:
                lines.append(f"  ? {name} [error]")

        return "\n".join(lines)

    def _get_status_indicator(self, repo: Repo) -> str:
        """Get status indicator for a repo"""
        try:
            if repo.is_dirty():
                return "*"
            elif len(list(repo.iter_commits(f'{repo.active_branch}@{{u}}..{repo.active_branch}'))) > 0:
                return "^"
            else:
                return "+"
        except:
            return "+"

    def get_project_status(self, project_name: str) -> str:
        """Get detailed status of a specific project"""
        repo = self.repos.get(project_name)

        if not repo:
            for name, r in self.repos.items():
                if project_name.lower() in name.lower():
                    repo = r
                    project_name = name
                    break

        if not repo:
            return f"Project '{project_name}' not found."

        try:
            lines = [f"Project: {project_name}"]
            lines.append(f"  Path: {repo.working_dir}")
            lines.append(f"  Branch: {repo.active_branch.name}")

            if repo.is_dirty():
                changed = [item.a_path for item in repo.index.diff(None)]
                staged = [item.a_path for item in repo.index.diff('HEAD')]
                untracked = repo.untracked_files

                if changed:
                    lines.append(f"  Modified: {len(changed)} files")
                if staged:
                    lines.append(f"  Staged: {len(staged)} files")
                if untracked:
                    lines.append(f"  Untracked: {len(untracked)} files")
            else:
                lines.append("  Status: Clean")

            commits = list(repo.iter_commits(max_count=3))
            if commits:
                lines.append("  Recent commits:")
                for commit in commits:
                    date = datetime.fromtimestamp(commit.committed_date)
                    msg = commit.message.split('\n')[0][:50]
                    lines.append(f"    - {msg} ({date.strftime('%m/%d')})")

            return "\n".join(lines)

        except Exception as e:
            return f"Error getting status for {project_name}: {e}"

    def get_recent_activity(self, days: int = 7) -> str:
        """Get recent activity across all projects"""
        if not self.repos:
            return "No Git projects found."

        activity = []
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for name, repo in self.repos.items():
            try:
                for commit in repo.iter_commits(max_count=20):
                    if commit.committed_date >= cutoff:
                        activity.append({
                            'project': name,
                            'message': commit.message.split('\n')[0][:40],
                            'date': datetime.fromtimestamp(commit.committed_date),
                            'author': commit.author.name
                        })
            except:
                pass

        if not activity:
            return f"No commits in the last {days} days."

        activity.sort(key=lambda x: x['date'], reverse=True)

        lines = [f"Recent Git activity (last {days} days):"]

        current_date = None
        for item in activity[:15]:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str != current_date:
                current_date = date_str
                lines.append(f"\n  {item['date'].strftime('%A, %B %d')}:")

            lines.append(f"    [{item['project']}] {item['message']}")

        return "\n".join(lines)

    def get_dirty_projects(self) -> str:
        """List projects with uncommitted changes"""
        dirty = []

        for name, repo in self.repos.items():
            try:
                if repo.is_dirty() or repo.untracked_files:
                    changed = len([item for item in repo.index.diff(None)])
                    untracked = len(repo.untracked_files)
                    dirty.append({
                        'name': name,
                        'changed': changed,
                        'untracked': untracked
                    })
            except:
                pass

        if not dirty:
            return "All projects are clean. Nice work, sir."

        lines = ["Projects with uncommitted changes:"]
        for project in dirty:
            details = []
            if project['changed']:
                details.append(f"{project['changed']} modified")
            if project['untracked']:
                details.append(f"{project['untracked']} untracked")

            lines.append(f"  * {project['name']}: {', '.join(details)}")

        return "\n".join(lines)

    def get_project_summary(self) -> str:
        """Get a quick summary for the daily briefing"""
        if not self.repos:
            return "No Git projects configured."

        total = len(self.repos)
        dirty = sum(1 for r in self.repos.values() if self._is_dirty_safe(r))

        summary = f"{total} projects tracked"
        if dirty > 0:
            summary += f", {dirty} with uncommitted changes"

        return summary

    def _is_dirty_safe(self, repo: Repo) -> bool:
        """Safely check if repo is dirty"""
        try:
            return repo.is_dirty() or len(repo.untracked_files) > 0
        except:
            return False

    def refresh(self):
        """Refresh repository list"""
        self._scan_repos()
