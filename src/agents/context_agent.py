import os
import subprocess
from typing import List

from .base_agent import BaseAgent
from src.state import PipelineState


class ContextAgent(BaseAgent):
    """
    ContextAgent

    Gathers lightweight repository context describing *where* the commit
    is being made. The output is intentionally short (1–2 bullets) so it
    can be consumed by downstream agents without adding noise.
    """

    name = "context_agent"

    def _git(self, args: List[str], cwd: str) -> str:
        try:
            return subprocess.check_output(
                ["git"] + args,
                cwd=cwd,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except Exception:
            return ""

    def run(self, state: PipelineState) -> PipelineState:
        repo_path = state.repo_path or os.getcwd()

        git_root = self._git(["rev-parse", "--show-toplevel"], repo_path)
        branch = self._git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
        remote = self._git(["config", "--get", "remote.origin.url"], repo_path)

        bullets: List[str] = []

        if git_root:
            rel_path = os.path.relpath(repo_path, git_root)
            if rel_path == ".":
                bullets.append(f"Changes applied at repository root on branch `{branch}`.")
            else:
                bullets.append(
                    f"Changes made under `{rel_path}/` on branch `{branch}`."
                )

        if remote:
            bullets.append(f"Repository remote: {remote}.")

        # Enforce 1–2 bullets only
        state.context_bullets = bullets[:2]

        if state.debug:
            state.debug_log[self.name] = state.context_bullets

        return state