#!/usr/bin/env python3
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import GPT4All, LlamaCpp
import logging
import data
import os
import sys
from functools import partial
import json
import http.server
from constants import CHROMA_SETTINGS

# Port to send request to
PORT = 8000

stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    handlers=[stdout_handler],
    level=10,
    format='%(asctime)s %(levelname)s %(module)-8s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)



class Prompter():
    def __init__(self) -> None:
        load_dotenv()
        self.embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME")
        self.persist_directory = os.environ.get('PERSIST_DIRECTORY')
        self.model_type = os.environ.get('MODEL_TYPE')
        self.model_path = os.environ.get('MODEL_PATH')
        self.model_n_ctx = os.environ.get('MODEL_N_CTX')
        self.model_n_gpu_layers = os.environ.get('MODEL_N_GPU_LAYERS')
        self.target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS',4))
        self.docsmanager_path = os.environ.get('DOCSMANAGER_DIRECTORY')

        # Setup DB and LLM
        self.db_manager = data.gptManager(self.docsmanager_path)
        self.setup_llm()
        self.refresh_qa()


    def setup_llm(self):
        # Parse the command line arguments
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embeddings_model_name)
        # activate/deactivate the streaming StdOut callback for LLMs
        callbacks = [] # [StreamingStdOutCallbackHandler()]
        # Prepare the LLM
        match self.model_type:
            case "LlamaCpp":
                self.llm = LlamaCpp(model_path=self.model_path, n_ctx=self.model_n_ctx, callbacks=callbacks, verbose=False, n_gpu_layers=self.model_n_gpu_layers)
            case "GPT4All":
                self.llm = GPT4All(model=self.model_path, n_ctx=self.model_n_ctx, backend='gptj', callbacks=callbacks, verbose=False)
            case _default:
                logging.info(f"Model {self.model_type} not supported!")
                exit;

    def refresh_qa(self):
        self.db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings, client_settings=CHROMA_SETTINGS)
        retriever = self.db.as_retriever(search_kwargs={"k": self.target_source_chunks})
        self.qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=retriever, return_source_documents= False)

    def ingestion(self):
        # Add file to database
        # Save file to db
        # call ingest.py
        data.update_vdb(self.embeddings)
        # refresh self.db


    def prompt(self, query):
        res = self.qa(query)
        return res['result']


class Serve(http.server.BaseHTTPRequestHandler):

    def __init__(self, prompter, *args, **kwargs) -> None:
        self.prompter = prompter
        super().__init__(*args, **kwargs)

    # Allows the UI to send requests
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        str = "V1.0"
        self.wfile.write(str.encode('utf-8'))
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length).decode('utf-8')
        request = json.loads(data)

        request_type = request['request_type']
        request_content = request['content']
        response_json = {}
        response_code = 200
        
        if request_type == "prompt":
            assert request_content != str, "Prompt must be literal strings!!"
            session = request["session"] 
            logging.info(session)
            self.prompter.db_manager.insert_values(session, [["user", request_content]])
            response_content = self.prompter.prompt(request_content)
            self.prompter.db_manager.insert_values(session, [["AI", response_content]])

            response_json['content'] = response_content
            pass
        elif request_type == "ingestion":
            #TODO run ingestion methods here
            pass
        elif request_type == "new_sess":
            session_name = request_content
            self.prompter.db_manager.new_session(session_name)
        else:
            response_code = 404

        self.send_response(response_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response_json['code'] = response_code
        self.wfile.write(json.dumps(response_json).encode('utf-8'))




if __name__ == "__main__":
    server_address = ("", PORT)
    
    prompter = Prompter()
    handler = partial(Serve, prompter)
    http_server = http.server.HTTPServer(server_address, handler)
    logging.info("Server Started!")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass

    http_server.server_close()

 
