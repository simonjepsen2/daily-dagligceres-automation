import os
import sys
import traceback

from composio import Composio


print("🚀 Starting DagligCeres Instagram post...")


# ============================================================
# CONFIGURATION
# ============================================================

api_key = os.environ.get("COMPOSIO_API_KEY")

if not api_key:
    print("❌ COMPOSIO_API_KEY is missing from GitHub Secrets.")
    sys.exit(1)

# IMPORTANT:
# This must match the user/entity you use for your Composio
# connected Instagram and Google Drive accounts.
#
# If your Composio setup uses a different user ID, change this.
USER_ID = "default"


# ============================================================
# CONNECT TO COMPOSIO
# ============================================================

composio = Composio(
    api_key=api_key
)


try:

    # ========================================================
    # GET INSTAGRAM TOOLS
    # ========================================================

    print("📱 Loading Instagram tools...")

    instagram_tools = composio.tools.get(
        USER_ID,
        toolkits=["INSTAGRAM"]
    )

    print("Available Instagram tools:")

    for tool in instagram_tools:
        print(f"  - {tool.slug}")


    # ========================================================
    # GET INSTAGRAM ACCOUNT
    # ========================================================

    print("📊 Getting Instagram account information...")

    user_info_result = composio.tools.execute(
        "INSTAGRAM_GET_USER_INFO",
        user_id=USER_ID,
        arguments={
            "ig_user_id": "me"
        }
    )

    print(
        f"Instagram response: {user_info_result}"
    )


    # Depending on the SDK response structure,
    # the useful data may be in the returned object.
    #
    # Try to access it safely.

    if isinstance(user_info_result, dict):
        user_data = user_info_result.get(
            "data",
            user_info_result
        )
    else:
        user_data = user_info_result


    ig_user_id = user_data["id"]

    username = user_data.get(
        "username",
        "Unknown"
    )

    media_count = user_data.get(
        "media_count",
        0
    )

    day_number = media_count + 1


    print(f"👤 Instagram: @{username}")
    print(f"📅 Posting: Dag {day_number}")


    # ========================================================
    # GOOGLE DRIVE
    # ========================================================

    print("☁️ Loading Google Drive tools...")

    drive_tools = composio.tools.get(
        USER_ID,
        toolkits=["GOOGLEDRIVE"]
    )

    print("Available Google Drive tools:")

    for tool in drive_tools:
        print(f"  - {tool.slug}")


    # ========================================================
    # DOWNLOAD IMAGE
    # ========================================================

    print("⬇️ Downloading DagligCeres image...")

    download_result = composio.tools.execute(
        "GOOGLEDRIVE_DOWNLOAD_FILE",
        user_id=USER_ID,
        arguments={
            "fileId": "1FpB9exKU8IuOeUqQjgdg56fNFZy-Ty4E"
        }
    )


    print(
        f"Google Drive response: {download_result}"
    )


    # Extract returned data

    if isinstance(download_result, dict):
        download_data = download_result.get(
            "data",
            download_result
        )
    else:
        download_data = download_result


    image_url = (
        download_data[
            "downloaded_file_content"
        ]["s3url"]
    )


    if not image_url:
        raise RuntimeError(
            "Google Drive did not return an image URL."
        )


    print("✅ Image downloaded successfully.")


    # ========================================================
    # CREATE INSTAGRAM MEDIA CONTAINER
    # ========================================================

    print("📷 Creating Instagram media container...")


    container_result = composio.tools.execute(
        "INSTAGRAM_POST_IG_USER_MEDIA",
        user_id=USER_ID,
        arguments={
            "ig_user_id": ig_user_id,
            "image_url": image_url,
            "caption": f"Dag {day_number}"
        }
    )


    print(
        f"Container response: {container_result}"
    )


    if isinstance(container_result, dict):
        container_data = container_result.get(
            "data",
            container_result
        )
    else:
        container_data = container_result


    container_id = container_data["id"]


    print(
        f"✅ Container created: {container_id}"
    )


    # ========================================================
    # PUBLISH INSTAGRAM POST
    # ========================================================

    print("🚀 Publishing to Instagram...")


    publish_result = composio.tools.execute(
        "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        user_id=USER_ID,
        arguments={
            "ig_user_id": ig_user_id,
            "creation_id": container_id,
            "max_wait_seconds": 120
        }
    )


    print(
        f"Publish response: {publish_result}"
    )


    if isinstance(publish_result, dict):
        publish_data = publish_result.get(
            "data",
            publish_result
        )
    else:
        publish_data = publish_result


    media_id = publish_data.get(
        "id"
    )


    # ========================================================
    # SUCCESS
    # ========================================================

    print("")
    print("🎉 =================================")
    print("🎉 INSTAGRAM POST SUCCESSFUL")
    print("🎉 =================================")
    print(f"🎉 Account: @{username}")
    print(f"🎉 Caption: Dag {day_number}")
    print(f"🎉 Media ID: {media_id}")
    print("🎉 =================================")
    print("")


except Exception as e:

    print("")
    print("❌ =================================")
    print("❌ INSTAGRAM POST FAILED")
    print("❌ =================================")
    print(f"❌ Error: {e}")
    print("")

    traceback.print_exc()

    sys.exit(1)
    
