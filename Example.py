import asyncio
import logging
import socketio
from aiohttp import web, web_request
from aiohttp_cors import setup as cors_setup, ResourceOptions
from network_logger import NetworkLoggerBackend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Using Socket.io server
sio = socketio.AsyncServer(cors_allowed_origins="*")

# Create NetworkLogger
network_logger = NetworkLoggerBackend(
    log_directory="./network_logs",
    max_logs=10,
    enable_console_logging=True
)

# Socket.io events
@sio.event
async def connect(sid, environ, auth):
    """Handle mobile app connection"""
    logger.info(f"Mobile client connected: {sid}")

@sio.event
async def disconnect(sid):
    """Handle mobile app disconnection"""
    logger.info(f"Mobile client disconnected: {sid}")


# HTTP endpoint for logging
async def handle_network_logs(request: web_request.Request) -> web.Response:
    """Handle network log uploads"""
    try:
        data = await request.json()
        result = await network_logger.handle_log_upload(data, request.remote)
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def main():
    """Start server"""
    app = web.Application()
    
    # Setup CORS
    cors = cors_setup(app, defaults={
        "*": ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods="*")
    })
    
    # Add routes and CORS
    route = app.router.add_post('/api/logs/network', handle_network_logs)
    cors.add(route)
    
    # Attach Socket.io
    sio.attach(app)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    
    logger.info("NetworkLogger Server started on http://0.0.0.0:8000")
    logger.info("Socket.io available for mobile connections")
    logger.info("HTTP endpoint: POST /api/logs/network")
    
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())