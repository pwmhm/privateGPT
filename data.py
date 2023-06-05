#!/usr/bin/env python3
import os
import glob
from typing import List
from dotenv import load_dotenv
from multiprocessing import Pool
from tqdm import tqdm
import glob
import logging
import sqlite3

from langchain.document_loaders import (
    CSVLoader,
    EverNoteLoader,
    PDFMinerLoader,
    TextLoader,
    UnstructuredEmailLoader,
    UnstructuredEPubLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredODTLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from constants import CHROMA_SETTINGS


load_dotenv()
logger = logging.getLogger(__name__)

# Load environment variables
persist_directory = os.environ.get('PERSIST_DIRECTORY')
embeddings_model_name = os.environ.get('EMBEDDINGS_MODEL_NAME')
chunk_size = 500
chunk_overlap = 50

class dataManager():
    def __init__(self, dbpath=".", db_name="manager.db") -> None:
        self.db = os.path.join(dbpath, db_name)
        # Create the database
        if not os.path.exists(self.db):
            os.makedirs(dbpath, exist_ok=True)
            print(self.db)
            conn = sqlite3.connect(self.db)
            conn.close()

    def create_table(self, table_name, values: dict):
        conn = sqlite3.connect(self.db)

        cmd = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
        id integer PRIMARY KEY,
        {", ".join([" ".join([k, v, "NOT", "NULL"]) for k, v in values.items()])}
        );
        '''
        conn.execute(cmd)
        logger.info(f"Successfully created a database - {self.db}")
        conn.close()

    def drop_values(self, table_name, values:dict):
        conn = sqlite3.connect(self.db)
        for k, v in values.items():
            cmd = f"DELETE FROM {table_name} WHERE {k} = '{v}'"
            conn.execute(cmd)
        conn.close()

    def insert_values(self, table_name, values: list):
        conn = sqlite3.connect(self.db)

        id = conn.execute(f"SELECT max(id) FROM {table_name};")
        max_id = list([x for x in id][0])[0]
        max_id = 0 if not max_id else int(max_id)
        for idx, value in enumerate(values):
            try:
                cmd = f"INSERT into {table_name} VALUES({', '.join(['?']*(1+len(value)))})"
                payload = [max_id+1+idx] + value
                logger.info(payload)
                cursor = conn.cursor()
                cursor.execute(cmd, payload)
                conn.commit()
            except Exception as E:
                logger.error(E)
        conn.close()

        # conn.execute('''\
        # CREATE TABLE SOURCE_DOCUMENTS
        # (ID INT PRIMARY KEY NOT NULL,
        # PATH          TEXT NOT NULL);
        # ''')

# Custom document loaders
class MyElmLoader(UnstructuredEmailLoader):
    """Wrapper to fallback to text/plain when default does not work"""

    def load(self) -> List[Document]:
        """Wrapper adding fallback for elm without html"""
        try:
            try:
                doc = UnstructuredEmailLoader.load(self)
            except ValueError as e:
                if 'text/html content not found in email' in str(e):
                    # Try plain text
                    self.unstructured_kwargs["content_source"]="text/plain"
                    doc = UnstructuredEmailLoader.load(self)
                else:
                    raise
        except Exception as e:
            # Add file_path to exception message
            raise type(e)(f"{self.file_path}: {e}") from e

        return doc


# Map file extensions to document loaders and their arguments
LOADER_MAPPING = {
    ".csv": (CSVLoader, {}),
    # ".docx": (Docx2txtLoader, {}),
    ".doc": (UnstructuredWordDocumentLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".enex": (EverNoteLoader, {}),
    ".eml": (MyElmLoader, {}),
    ".epub": (UnstructuredEPubLoader, {}),
    ".html": (UnstructuredHTMLLoader, {}),
    ".md": (UnstructuredMarkdownLoader, {}),
    ".odt": (UnstructuredODTLoader, {}),
    ".pdf": (PDFMinerLoader, {}),
    ".ppt": (UnstructuredPowerPointLoader, {}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"}),
    # Add more mappings for other file extensions and loaders as needed
}


def load_single_document(file_path: str) -> List[Document]:
    ext = "." + file_path.rsplit(".", 1)[-1]
    if ext in LOADER_MAPPING:
        loader_class, loader_args = LOADER_MAPPING[ext]
        loader = loader_class(file_path, **loader_args)
        return loader.load()

    raise ValueError(f"Unsupported file extension '{ext}'")

def load_documents(source_dir: str, ignored_files: List[str] = []) -> List[Document]:
    """
    Loads all documents from the source documents directory, ignoring specified files
    """
    all_files = []
    for ext in LOADER_MAPPING:
        all_files.extend(
            glob.glob(os.path.join(source_dir, f"**/*{ext}"), recursive=True)
        )
    filtered_files = [file_path for file_path in all_files if file_path not in ignored_files]

    with Pool(processes=os.cpu_count()) as pool:
        results = []
        with tqdm(total=len(filtered_files), desc='Loading new documents', ncols=80) as pbar:
            for i, docs in enumerate(pool.imap_unordered(load_single_document, filtered_files)):
                results.extend(docs)
                pbar.update()

    return results

def process_documents(ignored_files: List[str] = [], source_directory: str = ".") -> List[Document]:
    """
    Load documents and split in chunks
    """
    logger.info(f"Loading documents from {source_directory}")
    documents = load_documents(source_directory, ignored_files)
    if not documents:
        logger.info("No new documents to load")
        return []
    logger.info(f"Loaded {len(documents)} new documents from {source_directory}")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = text_splitter.split_documents(documents)
    logger.info(f"Split into {len(texts)} chunks of text (max. {chunk_size} tokens each)")
    return texts

def does_vectorstore_exist(persist_directory: str) -> bool:
    """
    Checks if vectorstore exists
    """
    if os.path.exists(os.path.join(persist_directory, 'index')):
        if os.path.exists(os.path.join(persist_directory, 'chroma-collections.parquet')) and os.path.exists(os.path.join(persist_directory, 'chroma-embeddings.parquet')):
            list_index_files = glob.glob(os.path.join(persist_directory, 'index/*.bin'))
            list_index_files += glob.glob(os.path.join(persist_directory, 'index/*.pkl'))
            # At least 3 documents are needed in a working vectorstore
            if len(list_index_files) > 3:
                return True
    return False

def update_vdb(embeddings=None, source_dir="source_documents"):
    # Create embeddings
    if not embeddings:
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

    if does_vectorstore_exist(persist_directory):
        # Update and store locally vectorstore
        logger.info(f"Appending to existing vectorstore at {persist_directory}")
        db = Chroma(persist_directory=persist_directory, embedding_function=embeddings, client_settings=CHROMA_SETTINGS)
        collection = db.get()
        texts = process_documents([metadata['source'] for metadata in collection['metadatas']], source_dir)
        if not texts:
            logger.info("No new documents found, vectordb up to date.")
            return
        logger.info(f"Creating embeddings. May take some minutes...")
        db.add_documents(texts)
    else:
        # Create and store locally vectorstore
        logger.info("Creating new vectorstore")
        texts = process_documents(source_directory=source_dir)
        if not texts:
            logger.info("No new documents found, vectordb up to date.")
            return
        db = Chroma.from_documents(texts, embeddings, persist_directory=persist_directory, client_settings=CHROMA_SETTINGS)
    db.persist()
    db = None

class gptManager(dataManager):
    def __init__(self, dbpath=".", db_name="manager.db") -> None:
        super().__init__(dbpath, db_name)
        self.raw_docs_dir = os.path.join(dbpath, "src_docs")
        self.doc_manager = ["docs", {
            "doc_path": "TEXT"
        }]

        self.create_table(self.doc_manager[0], self.doc_manager[1])
        self.init_db()
        

    def init_db(self):
        conn = sqlite3.connect(self.db)
        
        # get already queried files 
        cmd = f"SELECT {list(self.doc_manager[1].keys())[0]} FROM {self.doc_manager[0]}"
        cur = conn.cursor()
        cur.execute(cmd)
        files = [ row[0] for row in cur.fetchall() ]
        docs = []
        for extensions in list(LOADER_MAPPING.keys()):
            files_toadd = [ [f"'{doc}'"] for doc in glob.glob(os.path.join(self.raw_docs_dir, f"*{extensions}")) if f"'{doc}'" not in files]
            docs.extend(files_toadd)

        logger.info(f"found {len(docs)} new files to add.")
        if docs:
            self.insert_values(self.doc_manager[0], docs)
            update_vdb(source_dir=self.raw_docs_dir)
        conn.close()


    def new_session(self):
        # TODO 
        title = "session-xxx"
        values = {
            "user": "TEXT",
            "message": "TEXT"
        }
        self.create_table(title, values)
