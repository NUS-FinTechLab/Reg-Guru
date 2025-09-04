from multiprocessing import Pool, current_process
import os
import json
import rdflib
from rdflib import Namespace
from rdflib.namespace import OWL, SKOS, RDFS
from dotenv import load_dotenv

load_dotenv(override=True)
metadata_folder = os.getenv("EU_METADATA_PATH")
work_metadata_mapping = os.getenv("EU_WORK_METADATA_MAPPING_PATH")
work_eurovoc_mapping = os.getenv("EU_WORK_EUROVOC_MAPPING_PATH")
work_celex_mapping = os.getenv("EU_WORK_CELEX_MAPPING_PATH")
CDM = Namespace("http://publications.europa.eu/ontology/cdm#")

def get_pref_label(obj, g):
    name = None
    for label in g.objects(subject=obj, predicate=SKOS.prefLabel):
        name = label.toPython()
        break

    if not name:  # fallback to rdfs:label
        for label in g.objects(subject=obj, predicate=RDFS.label):
            name = label.toPython()
            break

    if not name:
        return obj
    else:
        return name

def process_metadata_batch(rows):
    pid = current_process().pid

    results = []
    batch_idx = 0
    for idx, row in rows.iterrows():
        work_id = row["work-id"]
        celex_expr_id = row["celex-expr-id"]
        celex_man_id = row["celex-man-id"]
        celex_cs_id = row["celex-cs-id"]
        celex_number = None
        cellar_uri = None

        eurovoc_code = []
        date_publication = None
        # date_modified = None
        # date_end = None
        date_expiration = None
        date_entry_into_force = None
        created_agent = None
        authored_agent = None
        contributed_agent = None

        mtd_path = os.path.join(metadata_folder, work_id, "tree_non_inferred.rdf")
        if not os.path.exists(mtd_path):
            continue
        try:
            g = rdflib.Graph()
            g.parse(mtd_path, format="xml")
        except Exception as e:
            print(f"[{pid}] Failed to parse {mtd_path} (format xml): {e}")
            continue

        # Eurovoc codes
        for subj, obj in g.subject_objects(CDM.work_is_about_concept_eurovoc):
            eurovoc_code.append(str(obj).split("/")[-1])

        # Celex number (get first match)
        celex_number = next(g.objects(None, CDM.resource_legal_id_celex), None)
        if not celex_number:
            celex_number = next(g.objects(None, CDM.celex_number), None)
        
        # If has celex number, get cellar uri, cellar man id, and cellar cs id (item identifier)
        celex_uri = rdflib.URIRef(f"http://publications.europa.eu/resource/celex/{celex_number}.{celex_expr_id}.{celex_man_id}.{celex_cs_id}")
        try:
            cellar_uri = next(g.subjects(predicate=OWL.sameAs, object=celex_uri))
        except Exception as e:
            # print(f"[{pid}] Failed to get cellar_uri for {celex_uri}: {e}")
            continue
        
        date_publication = next(g.objects(None, CDM.work_date_publication), None)
        date_expiration = next(g.objects(None, CDM.date_expiration), None)
        entry_date_uri = rdflib.URIRef("http://publications.europa.eu/ontology/cdm#date_entry-into-force")
        date_entry_into_force = next(g.objects(None, entry_date_uri), None)
        created_agent = next((get_pref_label(obj, g) for obj in g.objects(None, CDM.work_created_by_agent)), None)
        authored_agent = next((get_pref_label(obj, g) for obj in g.objects(None, CDM.work_authored_by_agent)), None)
        contributed_agent = next((get_pref_label(obj, g) for obj in g.objects(None, CDM.work_contributed_to_by_agent)), None)


        """
        for subj, pred, obj in g:
            # Check eurovoc codes
            if str(pred) == "http://publications.europa.eu/ontology/cdm#work_is_about_concept_eurovoc":
                code = obj.split("/")[-1]
                eurovoc_code.append(code)
            # Check celex numbers
            elif not celex_number and str(pred) in [
                "http://publications.europa.eu/ontology/cdm#resource_legal_id_celex",
                "http://publications.europa.eu/ontology/cdm#celex_number"
            ]:
                celex_number = obj
                # If has celex number, get cellar uri, cellar man id, and cellar cs id (item identifier)
                celex_uri = rdflib.URIRef(f"http://publications.europa.eu/resource/celex/{celex_number}.{celex_expr_id}.{celex_man_id}.{celex_cs_id}")
                try:
                    for uri in g.subjects(predicate=OWL.sameAs, object=celex_uri):
                        cellar_uri = uri
                        break
                except Exception as e:
                    print(f"[{pid}] Failed to iterate subjects as cellar_uri for {celex_uri}: {e}")
                    continue
            # Check for author
            elif str(pred) == "http://publications.europa.eu/ontology/cdm#work_created_by_agent":
                created_agent = get_pref_label(obj, g)
            elif str(pred) == "http://publications.europa.eu/ontology/cdm#work_authored_by_agent":
                authored_agent = get_pref_label(obj, g)
            elif str(pred) == "http://publications.europa.eu/ontology/cdm#work_contributed_to_by_agent":
                contributed_agent = get_pref_label(obj, g)
            elif str(pred) == "http://publications.europa.eu/ontology/cdm#work_date_publication":
                date_publication = obj
            elif str(pred) == "http://publications.europa.eu/ontology/cdm#work_date_modified":
                date_modified = obj
        """      


        meta = row.to_dict()
        meta.update({
            "celex-number": str(celex_number) if celex_number else celex_number,
            "cellar-uri": str(cellar_uri) if cellar_uri else cellar_uri,
            "eurovoc-codes": eurovoc_code,
            "date-publication": date_publication,
            "date-entry-into-force": date_entry_into_force,
            "date-expiration": date_expiration,
            "created-agent": created_agent,
            "authored-agent": authored_agent,
            "contributed-agent": contributed_agent
        })
        results.append(meta)

        if (idx + 1) % 1000 == 0:
            outfile = os.path.join(work_metadata_mapping, f"{pid}_{batch_idx}.json")
            with open(outfile, "w") as f:
                json.dump(results, f, indent=4)
            print(f"[{pid}] Saved batch {batch_idx} with {len(results)} records")
            results = []
            batch_idx += 1

    if results:
        outfile = os.path.join(work_metadata_mapping, f"{pid}_{batch_idx}.json")
        with open(outfile, "w") as f:
            json.dump(results, f, indent=4)
        print(f"[{pid}] Final save: batch {batch_idx} with {len(results)} records")
        # print(results)
    
    return True

#################################
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
