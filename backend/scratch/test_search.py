import os
import sys

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.regulation_service import RegulationService
from app.config import settings

def test_search():
    print("--- Testing Regulation Search Mechanism ---")
    reg_service = RegulationService(regulation_path=settings.REGULATION_FILE)
    
    queries = ["setback", "FAR", "residential", "sloping roof", "parking"]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        results = reg_service.search(query, limit=2)
        if not results:
            print("  No results found.")
        for res in results:
            print(f"  [ID {res['id']}] {res['title']}")
            print(f"  Snippet: {res['content'][:100]}...")

if __name__ == "__main__":
    test_search()
