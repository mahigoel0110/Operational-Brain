from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import logging

from app.services.ai.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_workspace_graph(
    workspace_id: str = Query(None, description="Filter graph by workspace id (currently global)"),
    limit: int = Query(500, description="Max number of nodes to return")
):
    """
    Returns the knowledge graph for a given workspace.
    """
    try:
        graph_data = await neo4j_client.get_workspace_graph(limit=limit)
        return graph_data
    except Exception as e:
        logger.error(f"Error getting workspace graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve graph data")

@router.get("/search")
async def search_graph(
    q: str = Query(..., description="Entity name search query"),
    workspace_id: str = Query(None, description="Filter graph by workspace id (currently global)")
):
    """
    Searches the knowledge graph by entity name.
    """
    try:
        graph_data = await neo4j_client.search_graph(query_str=q)
        return graph_data
    except Exception as e:
        logger.error(f"Error searching graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to search graph")

@router.get("/entity/{entity_id}")
async def get_entity_details(
    entity_id: str
):
    """
    Retrieves full metadata and 1-hop relationships for a specific entity.
    """
    try:
        details = await neo4j_client.get_entity_details(entity_id=entity_id)
        if not details:
            raise HTTPException(status_code=404, detail="Entity not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entity details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entity details")
