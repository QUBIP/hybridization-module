import os
import json

# File to store key streams
KEY_STREAM_FILE = "./data/key_streams.json"

def load_key_streams():
    """"
    Load key stream data from the file store, creating the file if it doesn't exist.

    Returns:
        dict: Key stream data loaded from the file.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(KEY_STREAM_FILE), exist_ok=True)

    # Check if the file exists
    if not os.path.exists(KEY_STREAM_FILE):
        # If the file does not exist, create an empty file
        with open(KEY_STREAM_FILE, "w") as f:
            json.dump({}, f)  # Initialize with an empty dictionary

    # Load the data from the file
    with open(KEY_STREAM_FILE, "r") as f:
        return json.load(f)

def save_key_streams(key_streams):
    """
    Save key stream data to the file store.

    Args:
        key_streams (dict): Key stream data to be saved.
    """
    with open(KEY_STREAM_FILE, "w") as f:
        json.dump(key_streams, f)

def delete_key_streams():
    """
    Deletes the key stream file if it exists and removes its folder if empty.


    Returns:
        dict: A status dictionary indicating success or failure.
    """
    if os.path.exists(KEY_STREAM_FILE):
        try:
            # Remove the file
            os.remove(KEY_STREAM_FILE)

            # Check if the folder is empty and remove it
            key_stream_folder = os.path.dirname(KEY_STREAM_FILE)
            if not os.listdir(key_stream_folder):
                os.rmdir(key_stream_folder)
            return {"status": 0}  # Success
        except Exception as e:
            return {"status": 1, "message": str(e)}  # Failure
    else:
        return {"status": 1, "message": "Key stream file does not exist"}