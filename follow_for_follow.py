import os
import sys
import traceback
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from composio import Composio


# ============================================================
# CONFIGURATION
# ============================================================

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "simonjepsen2@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "hbbc pvvt yytw fhbd")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", "simonjepsen2@gmail.com")

USER_ID = "pg-test-469e4bb8-661d-424b-91f3-dd8309694059"

# Limit for follows per session
MAX_FOLLOWS = 100

# Limit for unfollows per session
MAX_UNFOLLOWS = 100

# File to track previous followers
FOLLOWERS_FILE = "followers_history.json"

# File to track daily follower counts
FOLLOWER_STATS_FILE = "follower_stats.json"


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


def load_follower_stats():
    """Load previous follower statistics"""
    if os.path.exists(FOLLOWER_STATS_FILE):
        try:
            with open(FOLLOWER_STATS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load follower stats: {e}")
            return {}
    return {}


def save_follower_stats(stats):
    """Save follower statistics"""
    try:
        with open(FOLLOWER_STATS_FILE, 'w') as f:
            json.dump(stats, f)
    except Exception as e:
        print(f"⚠️  Could not save follower stats: {e}")


def extract_list_data(result):
    """Extract list data from Composio API response"""
    if isinstance(result, list):
        return result
    elif isinstance(result, dict):
        if "data" in result:
            data = result["data"]
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                inner_data = data["data"]
                if isinstance(inner_data, list):
                    return inner_data
    return []


def send_email_alert(subject, message, follower_count, previous_count):
    """Send email alert if follower count increases"""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("⚠️  Email credentials not configured. Skipping email alert.")
        return False

    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT
        msg['Subject'] = subject

        # Create HTML email body
        html_body = f"""
        <html>
            <body>
                <h2>{subject}</h2>
                <p><strong>Alert:</strong> {message}</p>
                <hr>
                <p><strong>Current Followers:</strong> {follower_count}</p>
                <p><strong>Previous Followers:</strong> {previous_count}</p>
                <p><strong>Growth:</strong> +{follower_count - previous_count}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p><em>This is an automated message from your Instagram automation bot.</em></p>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # Send email via Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"✅ Email alert sent to {EMAIL_RECIPIENT}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


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
            "limit": 200,
        },
    )

    print(f"📊 DEBUG - Raw followers result type: {type(followers_result)}")
    print(f"📊 DEBUG - Raw followers result: {str(followers_result)[:500]}")

    current_followers = extract_list_data(followers_result)
    current_follower_ids = {str(f.get("id")) for f in current_followers if isinstance(f, dict) and f.get("id")}
    
    print(f"✅ Retrieved {len(current_followers)} current followers.")
    print(f"📊 DEBUG - Follower IDs: {list(current_follower_ids)[:5]}...")


    # ========================================================
    # STEP 3.5 — CHECK FOLLOWER COUNT INCREASE
    # ========================================================

    print("")
    print("📈 Checking follower growth...")

    current_follower_count = len(current_followers)
    follower_stats = load_follower_stats()
    today = datetime.now().strftime("%Y-%m-%d")

    if today in follower_stats:
        previous_follower_count = follower_stats[today]
        print(f"📊 Today's previous count: {previous_follower_count}")
        print(f"📊 Current count: {current_follower_count}")

        if current_follower_count > previous_follower_count:
            growth = current_follower_count - previous_follower_count
            print(f"📈 Follower growth detected: +{growth}")

            # Send email alert
            send_email_alert(
                subject=f"🎉 Instagram Followers Growth Alert - +{growth}",
                message=f"Your Instagram account @{username} gained followers! New followers today: +{growth}",
                follower_count=current_follower_count,
                previous_count=previous_follower_count
            )
    else:
        print(f"📊 First check of the day. Current: {current_follower_count}")

    # Save today's follower count
    follower_stats[today] = current_follower_count
    save_follower_stats(follower_stats)


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
            "limit": 200,
        },
    )

    print(f"📊 DEBUG - Raw following result type: {type(following_result)}")
    print(f"📊 DEBUG - Raw following result: {str(following_result)[:500]}")

    current_following = extract_list_data(following_result)
    currently_following_ids = {str(f.get("id")) for f in current_following if isinstance(f, dict) and f.get("id")}
    
    print(f"✅ Currently following {len(current_following)} accounts.")
    print(f"📊 DEBUG - Following IDs: {list(currently_following_ids)[:5]}...")


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
    new_followers = [f for f in current_followers if isinstance(f, dict) and str(f.get("id")) in new_followers_ids]

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
    unfollowers = [f for f in current_following if isinstance(f, dict) and str(f.get("id")) in following_ids_not_followers]

    print(f"✅ Found {len(unfollowers)} accounts that don't follow you back.")
    
    print(f"📊 DEBUG - Unfollowers: {[f.get('username') for f in unfollowers[:10]]}")

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
    print(f"🎉 Followers: {len(current_followers)}")
    print(f"🎉 Following: {len(current_following)}")
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
