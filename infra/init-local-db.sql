-- Initialize local development database
-- Creates both ragagent DB and litellm schema

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create litellm schema for LiteLLM proxy
CREATE SCHEMA IF NOT EXISTS litellm;
