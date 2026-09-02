# pyrefly: ignore [missing-import] 
import pytest 
from pathlib import Path
from app.config import settings
from app.core.security import safe_path_resolve, validate_filename

def test_validate_filename():
    # Valid filenames
    assert validate_filename("document.pdf") == "document.pdf"
    assert validate_filename("my_notes_2026.md") == "my_notes_2026.md"
    
    # Path separator stripping
    assert validate_filename("../../secret.txt") == "secret.txt"
    assert validate_filename("C:\\Windows\\System32\\cmd.exe") == "cmd.exe"
    
    # Special character sanitization
    assert validate_filename("test:file*name?.pdf") == "test_file_name_.pdf"

def test_safe_path_resolve_valid():
    base_vault = settings.VAULT_DIR
    target = safe_path_resolve(base_vault, "subfolder/my_doc.md")
    assert target.is_relative_to(base_vault)
    assert target.name == "my_doc.md"

def test_safe_path_resolve_traversal_blocked():
    base_vault = settings.VAULT_DIR
    
    # Attempt to escape to parent directory
    with pytest.raises(ValueError, match="Security Violation"):
        safe_path_resolve(base_vault, "../../system_file.txt")
        
    with pytest.raises(ValueError, match="Security Violation"):
        safe_path_resolve(base_vault, "../db/ogcai.db")
