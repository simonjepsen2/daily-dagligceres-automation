import os
import sys
import traceback

from composio import Composio


# ============================================================
# CONFIGURATION
# ============================================================

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY")

USER_ID = "pg-test-469e4bb8-661d-424b-91f3-dd8309694059"

# Limit for follow-backs per session
MAX_FOLLOW_BACKS = 10

# Limit for engaging with followers
MAX_ENGAGEMENTS = 5


# ============================================================
# CHECK API KEY
# ============================================================

print("🚀 Starting Follow for Follow automation...")

if not COMPOSIO_API_KEY:
    print("❌ COMPOSIO_API_KEY is missing.")
    sys.exit(1)


# ============================================================
# CONNECT TO COMPOSIO
# ============================================================

composio = Composio(
    api_key=COMPOSIO_API_KEY,
    toolkit_versions={
        "instagram": "20260730_00",
    },
)


try:

    # ========================================================
    # STEP 1 — GET INSTAGRAM TOOLS
    # ========================================================

    print("")
    print("📱 Loading Instagram tools...")

    instagram_tools = composio.tools.get(
        user_id=USER_ID,
        toolkits=["INSTAGRAM"],
        limit=50,
    )

    print(f"✅ Loaded {len(instagram_tools)} Instagram tools.")


    # ========================================================
    # STEP 2 — GET INSTAGRAM USER INFO
    # ========================================================

    print("")
    print("📊 Getting Instagram account information...")

    user_info_result = composio.tools.execute(
        "INSTAGRAM_GET_USER_INFO",
        user_id=USER_ID,
        arguments={
            "ig_user_id": "me"
        },
    )

    # Extract user data
    user_data = user_info_result
    if isinstance(user_info_result, dict):
        if "data" in user_info_result:
            user_data = user_info_result["data"]
        if isinstance(user_data, dict) and "data" in user_data:
            user_data = user_data["data"]

    if not isinstance(user_data, dict):
        raise RuntimeError("Could not understand Instagram user response.")

    ig_user_id = user_data.get("id")
    username = user_data.get("username", "Unknown")

    if not ig_user_id:
        raise RuntimeError("Instagram user ID was not returned.")

    print(f"👤 Instagram account: @{username}")
    print(f"🆔 Instagram user ID: {ig_user_id}")


    # ========================================================
    # STEP 3 — GET FOLLOWER REQUESTS
    # ========================================================

    print("")
    print("👥 Checking for follow requests...")

    # Get pending follow requests
    follower_requests_result = composio.tools.execute(
        "INSTAGRAM_GET_FOLLOWER_REQUESTS",
        user_id=USER_ID,
        arguments={
            "ig_user_id": ig_user_id,
            "limit": MAX_FOLLOW_BACKS,
        },
    )

    # Extract follower requests data
    requests_data = follower_requests_result
    if isinstance(follower_requests_result, dict):
        if "data" in follower_requests_result:
            requests_data = follower_requests_result["data"]

    follower_requests = []
    if isinstance(requests_data, list):
        follower_requests = requests_data
    elif isinstance(requests_data, dict) and "data" in requests_data:
        follower_requests = requests_data.get("data", [])

    print(f"✅ Found {len(follower_requests)} follow request(s).")


    # ========================================================
    # STEP 4 — ACCEPT FOLLOW REQUESTS (FOLLOW BACK)
    # ========================================================

    if follower_requests:
        print("")
        print("🔗 Processing follow requests...")

        follow_back_count = 0

        for requester in follower_requests[:MAX_FOLLOW_BACKS]:
            try:
                requester_id = requester.get("id")
                requester_username = requester.get("username", "Unknown")

                if not requester_id:
                    print(f"⚠️  Skipping: Could not get ID for {requester_username}")
                    continue

                # Follow back the requester
                follow_result = composio.tools.execute(
                    "INSTAGRAM_FOLLOW_USER",
                    user_id=USER_ID,
                    arguments={
                        "ig_user_id": ig_user_id,
                        "user_id_to_follow": requester_id,
                    },
                )

                print(f"✅ Followed back: @{requester_username}")
                follow_back_count += 1

            except Exception as follow_error:
                print(f"⚠️  Failed to follow @{requester_username}: {follow_error}")
                continue

        print(f"✅ Successfully followed back {follow_back_count} users.")

    else:
        print("ℹ️  No pending follow requests.")


    # ========================================================
    # STEP 5 — ENGAGE WITH RECENT FOLLOWERS
    # ========================================================

    print("")
    print("💬 Engaging with recent followers...")

    followers_result = composio.tools.execute(
        "INSTAGRAM_GET_FOLLOWERS",
        user_id=USER_ID,
        arguments={
            "ig_user_id": ig_user_id,
            "limit": MAX_ENGAGEMENTS,
        },
    )

    # Extract followers data
    followers_data = followers_result
    if isinstance(followers_result, dict):
        if "data" in followers_result:
            followers_data = followers_result["data"]

    followers = []
    if isinstance(followers_data, list):
        followers = followers_data
    elif isinstance(followers_data, dict) and "data" in followers_data:
        followers = followers_data.get("data", [])

    print(f"✅ Retrieved {len(followers)} recent followers.")

    if followers:
        print("")
        print("📸 Liking recent posts from followers...")

        engagement_count = 0

        for follower in followers[:MAX_ENGAGEMENTS]:
            try:
                follower_id = follower.get("id")
                follower_username = follower.get("username", "Unknown")

                if not follower_id:
                    print(f"⚠️  Skipping: Could not get ID for {follower_username}")
                    continue

                # Get recent media from follower
                media_result = composio.tools.execute(
                    "INSTAGRAM_GET_USER_MEDIA",
                    user_id=USER_ID,
                    arguments={
                        "ig_user_id": follower_id,
                        "limit": 1,
                    },
                )

                # Extract media data
                media_data = media_result
                if isinstance(media_result, dict):
                    if "data" in media_result:
                        media_data = media_result["data"]

                media_list = []
                if isinstance(media_data, list):
                    media_list = media_data
                elif isinstance(media_data, dict) and "data" in media_data:
                    media_list = media_data.get("data", [])

                if media_list:
                    latest_media = media_list[0]
                    media_id = latest_media.get("id")

                    if media_id:
                        # Like the post
                        like_result = composio.tools.execute(
                            "INSTAGRAM_LIKE_MEDIA",
                            user_id=USER_ID,
                            arguments={
                                "media_id": media_id,
                            },
                        )

                        print(f"❤️  Liked post from @{follower_username}")
                        engagement_count += 1

            except Exception as engagement_error:
                print(f"⚠️  Failed to engage with @{follower_username}: {engagement_error}")
                continue

        print(f"✅ Successfully engaged with {engagement_count} followers.")

    else:
        print("ℹ️  No recent followers to engage with.")


    # ========================================================
    # SUCCESS
    # ========================================================

    print("")
    print("🎉 =======================================")
    print("🎉 FOLLOW FOR FOLLOW COMPLETE!")
    print("🎉 =======================================")
    print(f"🎉 Account: @{username}")
    print("🎉 =======================================")


except Exception as error:

    print("")
    print("❌ =======================================")
    print("❌ FOLLOW FOR FOLLOW FAILED")
    print("❌ =======================================")
    print(f"❌ Error: {error}")
    print("")

    traceback.print_exc()

    sys.exit(1)
