"""
fetch_cuad.py — CUAD Dataset Ingestion
Downloads sample contracts from the HuggingFace CUAD dataset.
Usage: python fetch_cuad.py
"""
import os
os.environ["HF_HOME"] = os.path.join(os.getcwd(), ".hf_cache")

from datasets import load_dataset

def main():
    print("Loading CUAD dataset from HuggingFace...")
    # CUAD dataset on HF contains document texts and Q&A annotations.
    # We will just fetch a few unique full-text documents.
    dataset = load_dataset("theatticusproject/cuad", split="train", verification_mode="no_checks")
    
    samples_saved = 0
    target_samples = 3
    os.makedirs("examples", exist_ok=True)
    
    for i, row in enumerate(dataset):
        pdf_obj = row.get("pdf")
        if not pdf_obj:
            continue
            
        text_pages = []
        try:
            for page in pdf_obj.pages:
                text = page.extract_text()
                if text:
                    text_pages.append(text)
        except Exception as e:
            print(f"Failed to extract text from document {i}: {e}")
            continue
            
        full_text = "\f".join(text_pages)
        if len(full_text.strip()) > 500:
            file_path = f"examples/cuad_contract_{i+1}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            print(f"✓ Saved: {file_path}")
            samples_saved += 1
            if samples_saved >= target_samples:
                break

    print(f"\nDone! Downloaded {samples_saved} contracts to the 'examples/' directory.")
    print("You can run them through the swarm using: python run.py examples/<filename>.txt")

if __name__ == "__main__":
    main()
