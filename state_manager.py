# A simple in-memory state dictionary to keep track of user flow.
# In a real database, we would store this permanently.

# Structure:
# user_id: {
#    "state": "IDLE" | "AWAITING_TITLE" | "AWAITING_DESC" | "AWAITING_CUSTOM_THUMB" | "AWAITING_SRT",
#    "video_message_id": int,
#    "file_id": str,
#    "file_name": str,
#    "title": str,
#    "description": str,
#    "privacy": str,
#    "category": str,
#    "thumbnail_mode": str, # "CUSTOM" | "AUTO" | "NONE"
#    "custom_thumb_file_id": str,
#    "subtitle_mode": str, # "BUILT_IN" | "SEPARATE" | "NONE"
#    "separate_srt_file_id": str,
#    "built_in_stream_index": int
# }

user_data = {}


def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"state": "IDLE"}
    return user_data[user_id]


def update_user_data(user_id, **kwargs):
    data = get_user_data(user_id)
    data.update(kwargs)
    user_data[user_id] = data


def reset_user_data(user_id):
    if user_id in user_data:
        user_data[user_id] = {"state": "IDLE"}
