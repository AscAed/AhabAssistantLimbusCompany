import hashlib

import pytest

from utils.file_utils import sha256_file


def test_sha256_file_empty(tmp_path):
    """Test computing hash of an empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    
    expected_hash = hashlib.sha256(b"").hexdigest()
    assert sha256_file(empty_file) == expected_hash

def test_sha256_file_small(tmp_path):
    """Test computing hash of a small file."""
    small_file = tmp_path / "small.txt"
    content = b"hello world"
    small_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    assert sha256_file(small_file) == expected_hash
    
def test_sha256_file_large(tmp_path):
    """Test computing hash of a file larger than the 1MB chunk size."""
    large_file = tmp_path / "large.bin"
    # Create a 2.5 MB file to test the 1MB chunking logic
    chunk_size = 1024 * 1024
    content = b"a" * int(chunk_size * 2.5)
    large_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    assert sha256_file(large_file) == expected_hash

def test_sha256_file_string_path(tmp_path):
    """Test that the function accepts a string path."""
    test_file = tmp_path / "test.txt"
    content = b"test string path"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    assert sha256_file(str(test_file)) == expected_hash

def test_sha256_file_not_found():
    """Test that a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        sha256_file("nonexistent_file.txt")
