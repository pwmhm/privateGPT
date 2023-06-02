# privateGPT
See the main repository for more details. This fork is a private project originally aimed to dockerize privateGPT and find a way to use GPU support.

# Prerequisites

   - Docker
   - Nvidia-docker support
   - ...

# Running (WIP)

Build the container using the command below. It should take care of all dependencies automatically.

```shell
docker build -t privateGPT -f privateGPT.dockerfile .
```

# Getting the model

The dockerfile installs llama-cpp-python 0.1.52 specifically, you can look on HuggingFace for the models, just make sure it starts with "ggml".

# GPU Support

Currently, only LlamaCpp has been tested with GPU. Tested with [Vicuna 13B Q5](https://huggingface.co/vicuna/ggml-vicuna-13b-1.1/resolve/main/ggml-vic13b-uncensored-q5_1.bin).

# Development

Use this script to run the container for development purposes

```shell
docker run --network=host --gpus all --mount type=bind,source=$(pwd),target=/tmp/project -w /tmp/project --name privateGPT-dev -t privateGPT
```

# TODOS

   - [x] Dockerize privateGPT
   - [x] Add GPU support for either one of the models
   - [ ] Modify dockerfile such that deployment is automatic
   - [ ] Turn into HTTP server (kinda like a serverless type of thing?)
   - [ ] Create simple UI (kinda like ChatGPT UI)