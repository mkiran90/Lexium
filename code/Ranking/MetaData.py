import os
import json
from code.forward_index.ForwardIndex import ForwardIndex


forward_index = ForwardIndex()

class MetadataHandler:
    def __init__(self, forward_index, metadata_file='metadata.json'):
        self.forward_index = forward_index
        # Ensure the metadata file path is absolute
        self.metadata_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            metadata_file
        )
        print(f"Metadata file path: {self.metadata_file}")  # Debug print
        self.metadata = self.load_metadata()

    def load_metadata(self):
        """Load metadata from the file, or initialize it if it doesn't exist."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as file:
                    metadata = json.load(file)
                    print(f"Loaded metadata: {metadata}")  # Debug print
                    return metadata
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"Error loading metadata, initializing new data.")
                return {"avg_doc_length": 0, "doc_count": 0}
        
        # If no metadata exists, calculate average document length
        avg_doc_length, doc_count = self.calculate_initial_avg_doc_length()
        self.metadata = {"avg_doc_length": avg_doc_length, "doc_count": doc_count}  # Initialize metadata here
        print(f"Initialized metadata: {self.metadata}")  # Debug print
        self.save_metadata()  # Save metadata to file immediately
        return self.metadata  # Return the initialized metadata

    def save_metadata(self):
        """Save the current metadata to the file."""
        print(f"Saving metadata to: {self.metadata_file}")  # Debug print
        with open(self.metadata_file, 'w') as file:
            json.dump(self.metadata, file, indent=4)

    def calculate_initial_avg_doc_length(self):
        """Calculate the initial average document length using the forward index."""
        total_length = 0
        total_docs = self.forward_index.size()  # Assuming this returns the number of documents

        if total_docs == 0:
            print("No documents found!")
            return 0, 0  # Return zero if no documents

        for docID in range(total_docs):
            document = self.forward_index.get_document(docID) 
            total_length += self.calculate_body_words(document) 

        avg_doc_length = total_length / total_docs if total_docs > 0 else 0
        print(f"Avg Document Length Calculated: {avg_doc_length}")

        # Updating metadata with the newly calculated values
        self.metadata["avg_doc_length"] = avg_doc_length
        self.metadata["doc_count"] = total_docs
        
        # Saving the updated metadata immediately after calculation
        self.save_metadata()

        return avg_doc_length, total_docs

    def update_average_doc_length(self, new_doc_length):
        """Update the average document length dynamically."""
        old_avg = self.metadata["avg_doc_length"]
        old_doc_count = self.metadata["doc_count"]
        new_doc_count = old_doc_count + 1

        # Use this formula to update the average document length
        new_avg = old_avg + (new_doc_length - old_avg) / new_doc_count

        self.metadata["avg_doc_length"] = new_avg
        self.metadata["doc_count"] = new_doc_count
        self.save_metadata()

    def get_average_doc_length(self):
        """Get the average document length."""
        return self.metadata.get("avg_doc_length", 0)  

    def calculate_body_words(self, document):
        """Calculate the total number of body words in a document by counting word positions."""
        total_body_words = 0

        # Iterating over the document's body words and count the total number of positions
        for body_word in document.body_words:  
            total_body_words += len(body_word.positions)  # Each position gives us a word

        return total_body_words


if __name__ == "__main__":
    # Initialize ForwardIndex (ensure it's populated with data)
    metadata_handler = MetadataHandler(forward_index)

    # Calculate and display debug values
    total_length, total_docs = metadata_handler.calculate_initial_avg_doc_length()
    print(f"Document Count: {total_docs}")

    # Force saving metadata to ensure file creation
    metadata_handler.save_metadata()
    print("Metadata has been saved.")
