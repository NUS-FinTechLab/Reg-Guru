from multiprocessing import Pool, current_process
import os
import json
import rdflib
from dotenv import load_dotenv

load_dotenv()
metadata_folder = os.getenv("EU_METADATA_PATH")
work_eurovoc_mapping = os.getenv("EU_WORK_EUROVOC_MAPPING_PATH")
work_celex_mapping = os.getenv("EU_WORK_CELEX_MAPPING_PATH")

def get_eurovoc_batch(rows):
    """Process a batch of rows to extract Eurovoc codes from RDF files."""

    results = []
    pid = current_process().pid
    batch_idx = 0

    for idx, row in rows.iterrows():
        work_id = row["work-id"]
        path = os.path.join(metadata_folder, work_id, "tree_non_inferred.rdf")
        if not os.path.exists(path):
            continue
        try:
            g = rdflib.Graph()
            g.parse(path, format="xml")
            for subj, pred, obj in g:
                if str(pred) == "http://publications.europa.eu/ontology/cdm#work_is_about_concept_eurovoc":
                    code = obj.split("/")[-1]
                    results.append({"work-id": work_id, "eurovoc-code": code})
        except Exception as e:
            print(f"[{pid}] Failed to parse {work_id}: {e}")
        
        if (idx + 1) % 1000 == 0:
            outfile = os.path.join(work_eurovoc_mapping, f"{pid}_{batch_idx}.json")
            with open(outfile, "w") as f:
                json.dump(results, f, indent=4)
            print(f"[{pid}] Saved batch {batch_idx} with {len(results)} records")
            results = []
            batch_idx += 1

    if results:
        outfile = os.path.join(work_eurovoc_mapping, f"{pid}_{batch_idx}.json")
        with open(outfile, "w") as f:
            json.dump(results, f, indent=4)
        print(f"[{pid}] Final save: batch {batch_idx} with {len(results)} records")

    return True

def get_celex_batch(rows):
    """Process a batch of rows to extract Celex numbers from RDF files."""
    results = []
    pid = current_process().pid
    batch_idx = 0

    for idx, row in rows.iterrows():
        work_id = row["work-id"]
        path = os.path.join(metadata_folder, work_id, "tree_non_inferred.rdf")
        if not os.path.exists(path):
            continue
        try:
            g = rdflib.Graph()
            g.parse(path, format="xml")
            celex_number = None
            for subj, pred, obj in g:
                if str(pred) in [
                    "http://publications.europa.eu/ontology/cdm#resource_legal_id_celex",
                    "http://publications.europa.eu/ontology/cdm#celex_number"
                ]:
                    celex_number = obj
                    break
            
            if celex_number:
                results.append({"work-id": work_id, "celex": celex_number})
            else:
                results.append({"work-id": work_id, "celex": None})

        except Exception as e:
            print(f"[{pid}] Failed to parse {work_id}: {e}")
        
        if (idx + 1) % 1000 == 0:
            outfile = os.path.join(work_celex_mapping, f"{pid}_{batch_idx}.json")
            with open(outfile, "w") as f:
                json.dump(results, f, indent=4)
            print(f"[{pid}] Saved batch {batch_idx} with {len(results)} records")
            results = []
            batch_idx += 1

    if results:
        outfile = os.path.join(work_celex_mapping, f"{pid}_{batch_idx}.json")
        with open(outfile, "w") as f:
            json.dump(results, f, indent=4)
        print(f"[{pid}] Final save: batch {batch_idx} with {len(results)} records")

    return True