from fastapi import FastAPI
from api.router import hybrid
import logging

app = FastAPI()
app.include_router(hybrid.router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    import uvicorn
    import socket

    hostname = socket.gethostname()  # Gets the container’s DNS name
    ip_address = socket.gethostbyname(hostname)  # Gets the container’s internal IP

    logger.info(f"API is running at http://{hostname}:8000 (IP: {ip_address})")
    uvicorn.run(app, host='0.0.0.0', port=8000 , log_level="debug")
