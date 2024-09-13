import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

from chat import chain
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from graph_prefiltering import prefiltering_agent_executor
from importing import get_articles, import_cypher_query, process_params
from langserve import add_routes
from text2cypher import text2cypher_chain
from utils import graph, remove_null_properties, token_cost_process, setup_indices

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_WORKERS = min(os.cpu_count() * 5, 20)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/import_articles/")
def import_articles_endpoint() -> int:
    # if not article_data.query and not article_data.tag:
    #     raise HTTPException(
    #         status_code=500, detail="Either `query` or `tag` must be provided"
    #     )

    data = get_articles()
    
    # logging.info(f"Articles fetched: {len(data)} articles.")
    try:
        params = process_params(data)
    except Exception as e:
        # You could log the exception here if needed
        raise HTTPException(status_code=500, detail=e)
    graph.query(import_cypher_query, params={"data": params})
    logging.info(f"Article import query executed successfully.")
    return len(params)

@app.get("/fetch_network/")
def fetch_network() -> Dict:
    """
    Fetches data for network visualization
    """
    data = graph.query(
        """
CALL {
    MATCH (a:JobProfile)-[r]->(end)
    WHERE NOT end:Chunk
    WITH a,r,end
    WITH apoc.coll.toSet(collect(distinct a) + collect(distinct end)) AS nodes,
        collect(r) AS rels
    RETURN nodes,
           rels
UNION ALL
    MATCH (a:JobProfile)-[]->(end)
    WITH end
    MATCH (end)-[r]->(neighbor)
    WITH neighbor, r
    WITH collect(distinct neighbor) AS nodes,
         collect(r) AS rels
    RETURN nodes, rels
}
WITH collect(nodes) AS allNodeSets, collect(rels) AS allRelSets
WITH apoc.coll.flatten(allNodeSets) AS allNodes, apoc.coll.flatten(allRelSets) AS allRels
RETURN {nodes: [n in allNodes |
                {
                    id: coalesce(n.id),
                    tag: [el in labels(n) WHERE el <> "__Entity__"| el][0],
                    properties: n {.*}
                }] ,
        relationships: [r in allRels |
                    {start: coalesce(startNode(r).id, startNode(r).id, startNode(r).id),
                    end: coalesce(endNode(r).id, endNode(r).id, endNode(r).id),
                    type:type(r),
                    properties: r {.*}
                    }]
        } AS output
"""
    )
    return remove_null_properties(data[0]["output"])

add_routes(app, chain, path="/chat", enabled_endpoints=["stream_log"])

@app.get("/chat/stream_log")
def fetch_stream_log() -> str:
    print("Fetching stream log...")
    response = token_cost_process.get_cost_summary("gpt-4-turbo")
    return response

add_routes(
    app, text2cypher_chain, path="/text2cypher", enabled_endpoints=["stream_log"]
)
add_routes(
    app,
    prefiltering_agent_executor,
    path="/prefiltering",
    enabled_endpoints=["stream_log"],
)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
