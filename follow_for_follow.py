import os
import sys
import traceback
import json

from composio import Composio


# ============================================================
# CONFIGURATION
# ============================================================

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY")

USER_ID = "pg-test-469e4bb8-661d-424b-91f3-dd8309694059"

# Limit for follows per session
MAX_FOLLOWS = 20

# Limit for unfollows per session
MAX_UNFOLLOWS = 20

# File to track previous followers
FOLLOWERS_FILE = "followers_history.json"


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


def load_previous_followers():
    """Load the list of followers from previous run"""
    if os.path.exists(FOLLOWERS_FILE):
        try:
            with open(FOLLOWERS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load previous followers: {e}")
            return []
    return []


def save_followers(followers_list):
    """Save current followers list for next run"""
    try:
        with open(FOLLOWERS_FILE, 'w') as f:
            json.dump(followers_list, f)
    except Exception as e:
        print(f"⚠️  Could not save followers list: {e}")


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
    # STEP 3 — GET CURRENT FOLLOWERS
    # ========================================================

    print("")
    print("👥 Getting current followers...")

    followers_result = composio.tools.execute(
        "INSTAGRAM_GET_FOLLOWERS",
        user_id=USER_ID,
        arguments={
            "ig_user_id": ig_user_id,
            "limit": 100,
        },
    )

    # Extract followers data
    followers_data = followers_result
    if isinstance(followers_result, dict):
        if "data" in followers_result:
            followers_data = followers_result["data"]

    current_followers = []
    if isinstance(followers_data, list):
        current_followers = followers_data
    elif isinstance(followers_data, dict) and "data" in followers_data:
        current_followers = followers_data.get("data", [])

    current_follower_ids = {str(f.get("id")) for f in current_followers if f.get("id")}
    
    print(f"✅ Retrieved {len(current_followers)} current followers.")


    # ========================================================
    # STEP 4 — GET FOLLOWING LIST
    # ========================================================

    print("")
    print("👤 Getting following list...")

    following_result = composio.tools.execute(
        "INSTAGRAM_GET_FOLLOWING",
        user_id=USER_ID,
        arguments={
            "ig_user_id": ig_user_id,
            "limit": 100,
        },
    )

    # Extract following data
    following_data = following_result
    if isinstance(following_result, dict):
        if "data" in following_result:
            following_data = following_result["data"]

    current_following = []
    if isinstance(following_data, list):
        current_following = following_data
    elif isinstance(following_data, dict) and "data" in following_data:
        current_following = following_data.get("data", [])

    currently_following_ids = {str(f.get("id")) for f in current_following if f.get("id")}
    
    print(f"✅ Currently following {len(current_following)} accounts.")


    # ========================================================
    # STEP 5 — FIND NEW FOLLOWERS TO FOLLOW
    # ========================================================

    print("")
    print("🔗 Finding new followers to follow back...")

    # Get previous followers
    previous_followers = load_previous_followers()
    previous_follower_ids = set(previous_followers)

    # Find new followers (in current but not in previous)
    new_followers_ids = current_follower_ids - previous_follower_ids
    new_followers = [f for f in current_followers if str(f.get("id")) in new_followers_ids]

    # Filter: only follow those we're not already following
    to_follow = [f for f in new_followers if str(f.get("id")) not in currently_following_ids]

    print(f"✅ Found {len(new_followers)} new followers.")
    print(f"✅ {len(to_follow)} of them are not being followed yet.")

    if to_follow:
        print("")
        print("🔗 Following new followers...")

        follow_count = 0

        for follower in to_follow[:MAX_FOLLOWS]:
            try:
                follower_id = str(follower.get("id"))
                follower_username = follower.get("username", "Unknown")

                if not follower_id:
                    print(f"⚠️  Skipping: Could not get ID for {follower_username}")
                    continue

                # Follow the new follower
                follow_result = composio.tools.execute(
                    "INSTAGRAM_FOLLOW_USER",
                    user_id=USER_ID,
                    arguments={
                        "ig_user_id": ig_user_id,
                        "user_id_to_follow": follower_id,
                    },
                )

                print(f"✅ Followed: @{follower_username}")
                follow_count += 1

            except Exception as follow_error:
                print(f"⚠️  Failed to follow @{follower_username}: {follow_error}")
                continue

        print(f"✅ Successfully followed {follow_count} new followers.")

    else:
        print("ℹ️  No new followers to follow.")


    # ========================================================
    # STEP 6 — FIND UNFOLLOWERS (People we follow but don't follow us)
    # ========================================================

    print("")
    print("👋 Checking for unfollowers...")

    following_ids_not_followers = currently_following_ids - current_follower_ids
    unfollowers = [f for f in current_following if str(f.get("id")) in following_ids_not_followers]

    print(f"✅ Found {len(unfollowers)} accounts that don't follow you back.")

    if unfollowers:
        print("")
        print("👋 Unfollowing accounts that don't follow back...")

        unfollow_count = 0

        for unfollower in unfollowers[:MAX_UNFOLLOWS]:
            try:
                unfollower_id = str(unfollower.get("id"))
                unfollower_username = unfollower.get("username", "Unknown")

                if not unfollower_id:
                    print(f"⚠️  Skipping: Could not get ID for {unfollower_username}")
                    continue

                # Unfollow the account
                unfollow_result = composio.tools.execute(
                    "INSTAGRAM_UNFOLLOW_USER",
                    user_id=USER_ID,
                    arguments={
                        "ig_user_id": ig_user_id,
                        "user_id_to_unfollow": unfollower_id,
                    },
                )

                print(f"👋 Unfollowed: @{unfollower_username}")
                unfollow_count += 1

            except Exception as unfollow_error:
                print(f"⚠️  Failed to unfollow @{unfollower_username}: {unfollow_error}")
                continue

        print(f"✅ Successfully unfollowed {unfollow_count} accounts.")

    else:
        print("ℹ️  No unfollowers found.")


    # ========================================================
    # STEP 7 — SAVE CURRENT FOLLOWERS FOR NEXT RUN
    # ========================================================

    print("")
    print("💾 Saving followers list for next run...")

    follower_ids_list = list(current_follower_ids)
    save_followers(follower_ids_list)

    print(f"✅ Saved {len(follower_ids_list)} followers.")


    # ========================================================
    # SUCCESS
    # ========================================================

    print("")
    print("🎉 =======================================")
    print("🎉 FOLLOW FOR FOLLOW COMPLETE!")
    print("🎉 =======================================")
    print(f"🎉 Account: @{username}")
    print(f"🎉 New follows: {len(to_follow)} (up to {MAX_FOLLOWS})")
    print(f"🎉 Unfollows: {len(unfollowers)} (up to {MAX_UNFOLLOWS})")
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
