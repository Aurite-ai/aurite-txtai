import asyncio
import logging
from src.config import Settings
from src.services.redis import initialize_redis_services
from src.services import initialize_services
from src.models.messages import Message, MessageType
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_stream_communication():
    """Test basic stream communication between services"""
    try:
        # Initialize settings
        settings = Settings()
        logger.info("Settings initialized")

        # Initialize core services first
        core_services = await initialize_services(settings)
        logger.info("Core services initialized")

        # Initialize Redis services
        redis_services = await initialize_redis_services(settings, core_services)
        logger.info("Redis services initialized")

        # Get service instances
        comm_service = redis_services["communication"]
        stream_service = redis_services["stream"]

        # Start stream listener
        await stream_service.start_listening()
        logger.info("Stream listener started")

        # Test each stream type
        test_messages = [
            {
                "stream": settings.STREAM_EMBEDDINGS,
                "message": {
                    "type": MessageType.EMBEDDINGS_REQUEST.value,
                    "data": json.dumps({"text": "Test embedding"}),
                    "session_id": "test-embeddings",
                },
            },
            {
                "stream": settings.STREAM_LLM,
                "message": {
                    "type": MessageType.LLM_REQUEST.value,
                    "data": json.dumps({"prompt": "Say hello"}),
                    "session_id": "test-llm",
                },
            },
            {
                "stream": settings.STREAM_PERSONA,
                "message": {
                    "type": MessageType.RAG_REQUEST.value,
                    "data": json.dumps({"query": "What is AI?"}),
                    "session_id": "test-rag",
                },
            },
        ]

        for test in test_messages:
            logger.info(f"\nTesting {test['stream']}...")
            logger.info(f"Publishing message: {test['message']}")

            # Send message
            msg_id = await comm_service.publish_to_stream(test['stream'], test['message'])
            logger.info(f"Published message with ID: {msg_id}")

            # Wait for processing
            logger.info("Waiting for response...")
            await asyncio.sleep(2)

            # Read response
            response = await comm_service.read_stream(test['stream'])
            if response:
                logger.info(f"Received response: {response}")
            else:
                logger.warning(f"No response received for {test['stream']}")

            await asyncio.sleep(1)  # Brief pause between tests

        # Cleanup
        await stream_service.stop_listening()
        await comm_service.close()
        logger.info("Test complete")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_stream_communication())
