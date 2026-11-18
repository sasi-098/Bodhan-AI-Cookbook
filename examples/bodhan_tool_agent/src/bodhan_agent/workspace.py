"""Workspace sandbox guards and path traversal validation."""

from __future__ import annotations

from pathlib import Path


class SecurityError(Exception):
    """Raised when an operation attempts path traversal outside the approved workspace sandbox."""
    pass


class WorkspaceSandbox:
    """Restricts file access strictly to approved workspaces, input directories, and output targets."""

    def __init__(self, allowed_roots: list[str | Path]):
        self.allowed_roots = [Path(r).resolve() for r in allowed_roots if Path(r).exists()]
        # Add current working directory and outputs/cache by default
        self.allowed_roots.append(Path.cwd().resolve())

    def validate_path(self, path: str | Path, must_exist: bool = False) -> Path:
        """Validate that a target path resolves strictly inside allowed workspace directories.
        
        Raises SecurityError if path traversal is detected.
        """
        p = Path(path).resolve()

        if must_exist and not p.exists():
            raise FileNotFoundError(f"File not found within workspace: {path}")

        # Check if p is inside any allowed root
        is_safe = False
        for root in self.allowed_roots:
            try:
                p.relative_to(root)
                is_safe = True
                break
            except ValueError:
                continue

        if not is_safe:
            raise SecurityError(
                f"Security Sandbox Violation: Path '{path}' resolves outside the allowed workspace "
                f"directories ({[str(r) for r in self.allowed_roots]})."
            )

        return p
