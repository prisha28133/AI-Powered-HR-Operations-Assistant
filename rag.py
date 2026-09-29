import os
import re

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document


POLICY_FOLDER = "Policies"
VECTOR_DB_FOLDER = "vector_db"


# =========================================================
# EMBEDDING MODEL
# =========================================================

embedding = OllamaEmbeddings(
    model="nomic-embed-text"
)


# =========================================================
# LOAD EXISTING VECTOR DATABASE
# =========================================================

if os.path.exists(VECTOR_DB_FOLDER):

    vector_db = Chroma(
        persist_directory=VECTOR_DB_FOLDER,
        embedding_function=embedding
    )

    existing_data = vector_db.get()

    if existing_data and existing_data.get("ids"):

        print(
            f" Existing vector database loaded: "
            f"{len(existing_data['ids'])} chunks"
        )

    else:

        print(" Vector database is empty. Creating database...")
        vector_db = None

else:

    vector_db = None


# =========================================================
# CREATE VECTOR DATABASE
# =========================================================

if vector_db is None:

    print(" Loading HR policy PDFs...")

    loader = PyPDFDirectoryLoader(POLICY_FOLDER)

    documents = loader.load()

    rule_documents = []


    # =====================================================
    # PROCESS EACH POLICY PDF
    # =====================================================

    for doc in documents:

        source = os.path.basename(
            doc.metadata.get("source", "")
        ).lower()


        # -------------------------------------------------
        # IDENTIFY POLICY TYPE
        # -------------------------------------------------

        if "leave" in source:

            policy_type = "leave"

        elif "attendance" in source:

            policy_type = "attendance"

        elif "wfh" in source or "work_from_home" in source:

            policy_type = "wfh"

        elif "employee" in source or "information" in source:

            policy_type = "employee_information"

        else:

            policy_type = "unknown"


        # -------------------------------------------------
        # SPLIT TEXT INTO POLICY RULES
        # -------------------------------------------------

        text = doc.page_content

        # Split whenever a Rule such as:
        # Rule LP-001:
        # Rule AP-001:
        # Rule EI-001:
        # etc. appears.

        rule_parts = re.split(
            r'(?=Rule\s+[A-Z]{2}-\d+)',
            text,
            flags=re.IGNORECASE
        )


        for part in rule_parts:

            part = part.strip()

            if not part:
                continue


            # -------------------------------------------------
            # FIND RULE NUMBER
            # -------------------------------------------------

            rule_match = re.search(
                r'(Rule\s+[A-Z]{2}-\d+)',
                part,
                flags=re.IGNORECASE
            )


            if rule_match:

                rule_id = rule_match.group(1).upper()

            else:

                rule_id = "GENERAL"


            # -------------------------------------------------
            # CREATE DOCUMENT
            # -------------------------------------------------

            rule_document = Document(
                page_content=part,
                metadata={
                    "policy_type": policy_type,
                    "rule_id": rule_id,
                    "source": source
                }
            )

            rule_documents.append(rule_document)


    # =====================================================
    # CREATE VECTOR DATABASE
    # =====================================================

    vector_db = Chroma.from_documents(
        documents=rule_documents,
        embedding=embedding,
        persist_directory=VECTOR_DB_FOLDER
    )

    print(
        f" Vector database created with "
        f"{len(rule_documents)} policy rules"
    )


# =========================================================
# SEARCH POLICY
# =========================================================

def search_policy(query, policy_type):

    print("\n RAG SEARCH")
    print("Policy Type:", policy_type)
    print("Query:", query)


    # =====================================================
    # SEARCH POLICY TYPE
    # =====================================================

    results = vector_db.similarity_search(
        query,
        k=3,
        filter={
            "policy_type": policy_type
        }
    )


    # =====================================================
    # REMOVE DUPLICATE RULES
    # =====================================================

    unique_results = []

    seen_rules = set()


    for doc in results:

        rule_id = doc.metadata.get(
            "rule_id",
            "GENERAL"
        )

        if rule_id not in seen_rules:

            seen_rules.add(rule_id)

            unique_results.append(doc)


    # =====================================================
    # BUILD CONTEXT
    # =====================================================

    context = ""


    for i, doc in enumerate(
        unique_results,
        start=1
    ):

        rule_id = doc.metadata.get(
            "rule_id",
            "GENERAL"
        )

        print(
            f" Retrieved Rule {i}: {rule_id}"
        )


        context += (
            f"[{rule_id}]\n"
        )

        context += doc.page_content

        context += "\n\n"


    return context