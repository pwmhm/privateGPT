FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && apt-get install -y software-properties-common \
    && apt-get install -y build-essential python3-dev wget python3-distutils gcc git vim && \
    rm -rf /var/lib/apt/lists/*

# create a non-root user
ARG USER_ID=1000
RUN useradd -m --no-log-init --system  --uid ${USER_ID} appuser -g sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER appuser
WORKDIR /home/appuser

ENV PATH="/home/appuser/.local/bin:${PATH}"
RUN wget https://bootstrap.pypa.io/pip/get-pip.py && \
    python3 get-pip.py --user && \
    rm get-pip.py
RUN pip install --upgrade pip

# Build llama-cpp-python with GPU support
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=1"
ENV FORCE_CMAKE=1
ENV LLAMA_CUBLAS=1

# First copy the requirements.txt instead of everything so 
# The pip install layer is cached
COPY requirements.txt .
RUN pip install -r requirements.txt

# make document directories
RUN mkdir -p db/src_docs

# Then copy the rest
COPY . .

ENTRYPOINT [ "/bin/bash" ]
