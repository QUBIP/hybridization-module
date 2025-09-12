from fastapi import APIRouter, HTTPException, Response

from api.schemas import OpenConnectRequest, HybridKeyResponse, ErrorResponse
from api.driver import request_key
import json
router = APIRouter()

@router.post("/request_hybrid_key", responses={500: {"model": ErrorResponse}})
def post_request_hybrid_key(request: OpenConnectRequest):
    """Handles hybrid key negotiation requests"""
    try:
        response_data = request_key(request)
        print("\nHybrid Key Response successfully sent to API request:" + str(response_data))
        json_response = json.dumps(response_data, ensure_ascii=False) + "\n"
        return Response(content=json_response, media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))