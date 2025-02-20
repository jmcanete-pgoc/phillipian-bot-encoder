import redis
import os
import logging

logger = logging.getLogger(__name__)  # Get a logger instance

# Get Redis configuration from environment variables (BEST PRACTICE):
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")  # Default to 'redis' if env var not set
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))  # Default to 6379, convert to int
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

# Create a Redis connection pool (for better performance)
redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def get_redis_connection():  # Helper function to get a connection from the pool
    return redis.Redis(connection_pool=redis_pool)


def store_task_id(task_id, task_type, page_name):
    r = get_redis_connection()
    try:
        data_to_store = {
            "type": task_type,
            "page": page_name,
        }
        r.hset(f"task:{task_id}", mapping=data_to_store)  # Use a Redis hash
        r.sadd("active_tasks", task_id)  # Add task_id to set for easy retrieval
    finally:
        r.close()


def get_task_type(task_id):
    r = get_redis_connection()
    try:
        task_type = r.hget(f"task:{task_id}", "type")
        return task_type.decode('utf-8') if task_type else None  # Decode from bytes
    finally:
        r.close()


def get_task_details(task_id):
    r = get_redis_connection()

    def get_info(task_id):
        import json
        task_info = r.hgetall(f"task:{task_id}")

        if not task_info:  # Check if the key exists
            return None

        # Decode byte strings and parse JSON data (if any)
        decoded_task_info = {}
        for k, v in task_info.items():
            key = k.decode('utf-8')
            value = v.decode('utf-8')

            try:  # Attempt to parse as JSON; if fails, treat as regular string
                decoded_task_info[key] = json.loads(value)
            except json.JSONDecodeError:
                decoded_task_info[key] = value
        return decoded_task_info
    

    try:
        retrieved_info = get_info(task_id)
        # task_type = r.hget(f"task:{task_id}", "type")
        
        # Add other task details retrieval logic here if needed (e.g., status, start time)
        return {"task_id": task_id, "type": retrieved_info.get('type'), "page": retrieved_info.get('page')}  # Decode from bytes
    finally:
        r.close()





def get_all_stored_task_ids():
    r = get_redis_connection()
    try:
        return r.smembers('active_tasks')  # Get all task IDs from Redis
    finally:
        r.close()


def remove_task_id(task_id):
    r = get_redis_connection()
    try:
        r.delete(f"task:{task_id}")  # Delete the hash
        r.srem("active_tasks", task_id)  # Remove from the set
    finally:
        r.close()


def set_cancel_flag(task_id, boolean_value="False"):
    r = get_redis_connection()
    try:
        r.set(f"cancel_flag:{task_id}", boolean_value)  # Initialize the flag in Redis (as a string)
        return r  # Return the Redis connection (not necessary, but kept for consistency if needed)
    finally:
        r.close()


def delete_cancel_flag(task_id):
    r = get_redis_connection()
    try:
        r.delete(f"cancel_flag:{task_id}")  # Delete the flag after the task is done
    except Exception as e:
        logger.error(f"Error deleting cancellation flag from Redis: {e}")
    finally:
        r.close() # Return the connection to the pool


def store_import_count(user, count):
    r = get_redis_connection()
    try:
        r.hset(f"user:{user}", "count", count)  # Use a Redis hash
    finally:
        r.close()

def retrieve_import_count(user):
    r = get_redis_connection()
    try:
        count = r.get(f"count:")
        count = r.hget(f"user:{user}", "count")
        return count.decode('utf-8') if count else None  # Decode from bytes
    finally:
        r.close()