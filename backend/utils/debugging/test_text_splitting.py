import os
from dotenv import load_dotenv
import sys
import time

# Load environment variables
load_dotenv()

# Import the DocumentService class
from app.services.s3_service import S3Service
from app.services.document_service import DocumentService

def test_text_splitting(text, chunk_size=1500, overlap=300, test_name="Unnamed Test"):
    """Test the text splitting method directly"""
    print(f"\n{'='*80}")
    print(f"=== TEST: {test_name} ===")
    print(f"=== Text length={len(text)}, chunk_size={chunk_size}, overlap={overlap} ===")
    print(f"{'='*80}")
    
    # Initialize services
    s3_service = S3Service()
    document_service = DocumentService(s3_service)
    
    # Time the execution
    start_time = time.time()
    
    # Call the split_text method
    chunks = document_service._split_text(text, chunk_size, overlap)
    
    # Print results
    elapsed_time = time.time() - start_time
    print(f"\nRESULTS FOR: {test_name}")
    print(f"  Text length: {len(text)} characters")
    print(f"  Chunk size: {chunk_size}")
    print(f"  Overlap: {overlap}")
    print(f"  Number of chunks: {len(chunks)}")
    print(f"  Execution time: {elapsed_time:.2f} seconds")
    
    # Verify chunk sizes
    if chunks:
        min_size = min(len(chunk) for chunk in chunks)
        max_size = max(len(chunk) for chunk in chunks)
        avg_size = sum(len(chunk) for chunk in chunks) / len(chunks)
        print(f"  Chunk size statistics:")
        print(f"    Minimum: {min_size} characters")
        print(f"    Maximum: {max_size} characters")
        print(f"    Average: {avg_size:.1f} characters")
    
    # Check for overlapping content between adjacent chunks
    if len(chunks) > 1:
        print("\nChecking chunk overlaps...")
        for i in range(len(chunks) - 1):
            # Look for overlap between end of current chunk and start of next chunk
            current_end = chunks[i][-100:] if len(chunks[i]) > 100 else chunks[i]
            next_start = chunks[i+1][:100] if len(chunks[i+1]) > 100 else chunks[i+1]
            
            # Check if there's any overlap content
            overlap_found = False
            for j in range(1, min(len(current_end), len(next_start)) + 1):
                if current_end[-j:] == next_start[:j]:
                    print(f"  Overlap found between chunks {i} and {i+1}: '{current_end[-j:]}'")
                    overlap_found = True
                    break
            
            if not overlap_found and i < 3:  # Only show first few for brevity
                print(f"  No direct overlap between chunks {i} and {i+1}")
                print(f"    End of chunk {i}: '{current_end}'")
                print(f"    Start of chunk {i+1}: '{next_start}'")
    
    print(f"\nTEST COMPLETED: {test_name}")
    print(f"{'='*80}\n")
    return chunks

def create_test_text(paragraph_count=10, sentences_per_paragraph=5):
    """Create a test text with specified number of paragraphs and sentences"""
    paragraphs = []
    for i in range(paragraph_count):
        sentences = []
        for j in range(sentences_per_paragraph):
            sentences.append(f"This is sentence {j+1} in paragraph {i+1}. It contains random text for testing purposes.")
        paragraphs.append(" ".join(sentences))
    
    return "\n\n".join(paragraphs)

def create_problematic_text():
    """Create problematic text that might trigger the infinite loop bug"""
    # Very long text with no paragraph breaks
    return "This is a super long sentence without any paragraph breaks or easy places to split it. " * 200

def create_text_with_unusual_breaks():
    """Create text with unusual break patterns"""
    parts = []
    # No breaks at all
    parts.append("NobreaksataллNospacesNobreaksataллNospacesNobreaksataллNospacesNobreaksataллNospaces" * 20)
    # Unusual Unicode characters
    parts.append("Text with unusual—Unicode—characters—that—might—confuse—the—splitting—algorithm. " * 20)
    # Very short paragraphs
    parts.append("\n\n".join(["a"] * 50))
    return "\n\n".join(parts)

if __name__ == "__main__":
    # Test 1: Simple test with short text
    test_text = "This is a short test text. It should be processed as a single chunk."
    test_text_splitting(test_text, test_name="Short Text")
    
    # Test 2: Medium length text (single chunk but close to the limit)
    test_text = "This is a longer test text. " * 50
    test_text_splitting(test_text, test_name="Medium Text (Single Chunk)")
    
    # Test 3: Text with multiple chunks and clear paragraph breaks
    test_text = create_test_text(paragraph_count=10, sentences_per_paragraph=5)
    test_text_splitting(test_text, test_name="Text with Clear Paragraph Breaks")
    
    # Test 4: Longer text with multiple chunks
    test_text = create_test_text(paragraph_count=20, sentences_per_paragraph=10)
    test_text_splitting(test_text, test_name="Longer Text with Multiple Chunks")
    
    # Test 5: Problematic text that might trigger the infinite loop bug
    test_text = create_problematic_text()
    test_text_splitting(test_text, test_name="Problematic Text (Long with No Breaks)")
    
    # Test 6: Text with unusual break patterns
    test_text = create_text_with_unusual_breaks()
    test_text_splitting(test_text, test_name="Text with Unusual Break Patterns")
    
    # Test 7: Large overlap relative to chunk size
    test_text = create_test_text(paragraph_count=10, sentences_per_paragraph=5)
    test_text_splitting(test_text, chunk_size=1000, overlap=800, test_name="Large Overlap Relative to Chunk Size")
    
    # Test 8: Very small chunk size
    test_text = create_test_text(paragraph_count=5, sentences_per_paragraph=3)
    test_text_splitting(test_text, chunk_size=100, overlap=20, test_name="Very Small Chunk Size")
    
    # Test 9: Zero overlap
    test_text = create_test_text(paragraph_count=5, sentences_per_paragraph=3)
    test_text_splitting(test_text, chunk_size=1000, overlap=0, test_name="Zero Overlap")
    
    # Test 10: Extremely small text
    test_text = "a"
    test_text_splitting(test_text, test_name="Extremely Small Text")
    
    print("\n===== ALL TESTS COMPLETED =====")
    print("Inspect the results above to identify any issues with the text splitting algorithm.") 