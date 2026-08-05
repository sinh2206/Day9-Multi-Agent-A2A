#!/usr/bin/env bash
# Kaggle/Linux: Ollama auto-detects CUDA. Run in a dedicated process.
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=30m
ollama serve
