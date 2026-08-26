from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder  
from typing import Any

def response(
    status_code: int,
    message: str,
    data: Any = None,
    error: Any = None,
    count_data: int | None = None,
):
    resp = {
        "statusCode": status_code,
        "message": message,
    }
    if error is not None:
        resp["error"] = error
    if data is not None:
        resp["data"] = data
    if count_data is not None:
        resp["countData"] = count_data

    
    return JSONResponse(content=jsonable_encoder(resp), status_code=status_code)
