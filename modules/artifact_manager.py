"""
Artifact Manager Module.

Organizes and cleans up project artifacts.
"""

from pathlib import Path
from loguru import logger
import shutil


class ArtifactManager:
    """Manages project artifacts and file organization."""
    
    def organize(self, project_path: Path):
        """
        Organize project files into proper structure.
        
        Args:
            project_path: Path to project directory
        """
        logger.info(f"Organizing artifacts in {project_path}")
        
        # Ensure standard directories exist
        self._ensure_directories(project_path)
        
        # Move documentation files
        self._organize_docs(project_path)
        
        # Move logs
        self._organize_logs(project_path)
        
        # Clean up temporary files
        self._cleanup_temp_files(project_path)
        
        logger.info("Artifact organization complete")
    
    def _ensure_directories(self, project_path: Path):
        """Create standard directory structure."""
        directories = [
            "docs",
            "src",
            "tests",
            "logs",
            "config"
        ]
        
        for dir_name in directories:
            dir_path = project_path / dir_name
            dir_path.mkdir(exist_ok=True)
    
    def _organize_docs(self, project_path: Path):
        """Move documentation files to docs/ directory."""
        docs_dir = project_path / "docs"
        
        # Files that should be in docs/
        doc_extensions = ['.md', '.txt', '.pdf']
        doc_keywords = ['spec', 'plan', 'design', 'architecture']
        
        for file in project_path.iterdir():
            if not file.is_file():
                continue
            
            # Skip root-level important files
            if file.name in ['README.md', 'LICENSE', '.gitignore', 'requirements.txt']:
                continue
            
            # Move if it's a doc file
            if (file.suffix in doc_extensions or 
                any(kw in file.name.lower() for kw in doc_keywords)):
                
                target = docs_dir / file.name
                if not target.exists():
                    shutil.move(str(file), str(target))
                    logger.debug(f"Moved {file.name} to docs/")
    
    def _organize_logs(self, project_path: Path):
        """Move log files to logs/ directory."""
        logs_dir = project_path / "logs"
        
        for file in project_path.iterdir():
            if file.is_file() and (file.suffix == '.log' or 'log' in file.name.lower()):
                target = logs_dir / file.name
                if not target.exists() and file.parent != logs_dir:
                    shutil.move(str(file), str(target))
                    logger.debug(f"Moved {file.name} to logs/")
    
    def _cleanup_temp_files(self, project_path: Path):
        """Remove temporary and cache files safely."""
        # Safe patterns that are always temporary/cache files
        safe_glob_patterns = ['*.pyc', '*.pyo', '*.tmp']
        safe_dir_patterns = ['__pycache__']
        safe_file_patterns = ['.DS_Store', 'Thumbs.db', '.claude_instructions.md']

        # Protected files/directories that should never be deleted
        protected_names = {
            'src', 'tests', 'docs', 'config', 'logs',
            'README.md', 'LICENSE', '.gitignore', 'requirements.txt',
            'setup.py', 'pyproject.toml', 'package.json'
        }

        # Clean up glob patterns (safe temp files)
        for pattern in safe_glob_patterns:
            for file in project_path.rglob(pattern):
                if file.is_file() and file.name not in protected_names:
                    try:
                        file.unlink()
                        logger.debug(f"Removed temp file: {file}")
                    except OSError as e:
                        logger.warning(f"Could not remove {file}: {e}")

        # Clean up __pycache__ directories
        for pattern in safe_dir_patterns:
            for dir_path in project_path.rglob(pattern):
                if dir_path.is_dir() and dir_path.name not in protected_names:
                    try:
                        shutil.rmtree(dir_path)
                        logger.debug(f"Removed cache directory: {dir_path}")
                    except OSError as e:
                        logger.warning(f"Could not remove {dir_path}: {e}")

        # Clean up specific files only at project root level (not recursive)
        for pattern in safe_file_patterns:
            target = project_path / pattern
            if target.exists() and target.is_file():
                try:
                    target.unlink()
                    logger.debug(f"Removed: {pattern}")
                except OSError as e:
                    logger.warning(f"Could not remove {target}: {e}")
