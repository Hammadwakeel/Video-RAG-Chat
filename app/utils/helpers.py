# Generic helper functions

def chunk_list(lst, size):
    """Yield successive chunks from list."""
    for i in range(0, len(lst), size):
        yield lst[i:i+size]
