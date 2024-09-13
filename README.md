# QA System with GraphRAG

This project is designed to show an end-to-end pipeline for constructing knowledge graphs from job profiles and answer the questions with LLM based on the information provided from the knowledge graph.

The project uses Neo4j, a graph database, to store the knowledge graph. 
Lastly, the project uses OpenAI LLMs to provide a chat interface, which can answer questions based on the provided information from the knowledge graph.

## Setup

1. Set environment variables in `.env`. You can find the template in `.env.template`

2. Start the docker containers with

    ```
    docker compose up 
    ```

3. Open you favorite browser on `localhost:3000`
