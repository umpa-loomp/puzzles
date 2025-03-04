import pytest
from puzzle import Puzzle
from main import load_puzzles_from_file
import os
import tempfile

@pytest.fixture
def setup_puzzles():
    Puzzle.reset()
    yield
    Puzzle.reset()

def test_puzzle_creation(setup_puzzles):
    p = Puzzle("123456")
    assert p.puzzle_number == "123456"
    assert p.puzzle_sides["takes"] == "12"
    assert p.puzzle_sides["gives"] == "56"
    assert p.id == 0

def test_load_puzzles(setup_puzzles):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("123456\n234567\n345678\n")
        temp_path = f.name
    
    try:
        assert load_puzzles_from_file(temp_path)
        assert len(Puzzle.get_all_puzzles()) == 3
    finally:
        os.unlink(temp_path)

def test_find_longest_chain(setup_puzzles):
    # Create a chain: 1->2->3->4
    test_chain = [
        "104211",  # Takes 10, Gives 11
        "114212",  # Takes 11, Gives 12
        "124213",  # Takes 12, Gives 13
        "134214"   # Takes 13, Gives 14
    ]
    
    for puzzle in test_chain:
        Puzzle.add_puzzle_direct(puzzle)
    
    # Add non-chain puzzles
    Puzzle.add_puzzle_direct("204225")
    Puzzle.add_puzzle_direct("314232")
    
    chain = Puzzle.find_longest_chain(timeout_seconds=5)
    assert len(chain) == 4

@pytest.mark.integration
def test_api(setup_puzzles):
    import requests
    host = "http://localhost:5000"
    
    # Test puzzles endpoint
    r = requests.get(f"{host}/api/puzzles")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    
    # Test longest chain endpoint
    r = requests.get(f"{host}/api/puzzles/longest_chain")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)