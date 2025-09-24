from multiprocessing import Pool, current_process
import os
import json
import rdflib
metadata_folder = "data/LEG_MTD_20250709_22_36"
output_folder = "data/eurovoc/metadata_mapping"
def process_batch(rows):
    results = []
    pid = current_process().pid
    batch_idx = 0

    for idx, row in enumerate(rows):
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
            outfile = os.path.join(output_folder, f"{pid}_{batch_idx}.json")
            with open(outfile, "w") as f:
                json.dump(results, f, indent=4)
            print(f"[{pid}] Saved batch {batch_idx} with {len(results)} records")
            results = []
            batch_idx += 1

    if results:
        outfile = os.path.join(output_folder, f"{pid}_{batch_idx}.json")
        with open(outfile, "w") as f:
            json.dump(results, f, indent=4)
        print(f"[{pid}] Final save: batch {batch_idx} with {len(results)} records")

    return True