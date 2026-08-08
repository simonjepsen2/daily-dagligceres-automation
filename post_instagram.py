import os
import sys
import traceback

from composio import Composio


# ============================================================
# CONFIGURATION
# ============================================================

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY")

USER_ID = "pg-test-469e4bb8-661d-424b-91f3-dd8309694059"

GOOGLE_DRIVE_FILE_ID = "1FpB9exKU8IuOeUqQjgdg56fNFZy-Ty4E"


# ============================================================
# CHECK API KEY
# ============================================================

print("🚀 Starting DagligCeres Instagram automation...")

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
        "googledrive": "20260721_00",
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
    # STEP 2 — GET GOOGLE DRIVE TOOLS
    # ========================================================

    print("")
    print("☁️ Loading Google Drive tools...")

    drive_tools = composio.tools.get(
        user_id=USER_ID,
        toolkits=["GOOGLEDRIVE"],
        limit=100,
    )

    print(f"✅ Loaded {len(drive_tools)} Google Drive tools.")


    # ========================================================
    # STEP 3 — GET INSTAGRAM USER INFO
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

    print("Instagram response:")
    print(user_info_result)


    # ========================================================
    # EXTRACT USER DATA
    # ========================================================

    user_data = user_info_result

    if isinstance(user_info_result, dict):

        if "data" in user_info_result:
            user_data = user_info_result["data"]

        if (
            isinstance(user_data, dict)
            and "data" in user_data
        ):
            user_data = user_data["data"]


    if not isinstance(user_data, dict):
        raise RuntimeError(
            "Could not understand Instagram user response."
        )


    ig_user_id = user_data.get("id")

    username = user_data.get(
        "username",
        "Unknown"
    )

    media_count = user_data.get(
        "media_count",
        0
    )


    if not ig_user_id:
        raise RuntimeError(
            "Instagram user ID was not returned."
        )


    day_number = media_count + 1


    print(f"👤 Instagram account: @{username}")
    print(f"🆔 Instagram user ID: {ig_user_id}")
    print(f"📅 Today's post: Dag {day_number}")


    # ========================================================
    # STEP 4 — DOWNLOAD IMAGE FROM GOOGLE DRIVE
    # ========================================================

    print("")
    print("☁️ Downloading image from Google Drive...")

    download_result = composio.tools.execute(
        "GOOGLEDRIVE_DOWNLOAD_FILE",
        user_id=USER_ID,
        arguments={
            "file_id": GOOGLE_DRIVE_FILE_ID
        },
    )


    print("Google Drive response received.")


    # ========================================================
    # EXTRACT IMAGE URL
    # ========================================================

    download_data = download_result

    if isinstance(download_result, dict):

        if "data" in download_result:
            download_data = download_result["data"]

        if (
            isinstance(download_data, dict)
            and "data" in download_data
        ):
            download_data = download_data["data"]


    if not isinstance(download_data, dict):
        raise RuntimeError(
            "Could not understand Google Drive response."
        )


    downloaded_content = download_data.get(
        "downloaded_file_content"
    )


    if not downloaded_content:
        raise RuntimeError(
            "Google Drive did not return downloaded file content."
        )


    image_url = downloaded_content.get("s3url")


    if not image_url:
        raise RuntimeError(
            "Google Drive did not return an S3 URL."
        )


    print("✅ Image downloaded.")
    print("✅ Temporary image URL received.")


    # ========================================================
    # STEP 5 — CREATE INSTAGRAM MEDIA CONTAINER
    # ========================================================

    print("")
    print("📷 Creating Instagram media container...")

    container_result = composio.tools.execute(
        "INSTAGRAM_POST_IG_USER_MEDIA",
        user_id=USER_ID,
        arguments={
            "ig_user_id": ig_user_id,
            "image_url": image_url,
            "caption": f"Dag {day_number}",
        },
    )


    print("Instagram container response:")
    print(container_result)


    # ========================================================
    # EXTRACT CONTAINER ID
    # ========================================================

    container_data = container_result

    if isinstance(container_result, dict):

        if "data" in container_result:
            container_data = container_result["data"]

        if (
            isinstance(container_data, dict)
            and "data" in container_data
        ):
            container_data = container_data["data"]


    if not isinstance(container_data, dict):
        raise RuntimeError(
            "Could not understand Instagram container response."
        )


    container_id = container_data.get("id")


    if not container_id:
        raise RuntimeError(
            "Instagram did not return a container ID."
        )


    print(
        f"✅ Instagram container created: {container_id}"
    )


    # ========================================================
    # STEP 6 — PUBLISH TO INSTAGRAM
    # ========================================================

    print("")
    print("🚀 Publishing to Instagram...")

    publish_result = composio.tools.execute(
        "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        user_id=USER_ID,
        arguments={
            "ig_user_id": ig_user_id,
            "creation_id": container_id,
            "max_wait_seconds": 120,
        },
    )


    print("Instagram publish response:")
    print(publish_result)


    # ========================================================
    # SUCCESS
    # ========================================================

    print("")
    print("🎉 =======================================")
    print("🎉 INSTAGRAM POST SUCCESSFUL!")
    print("🎉 =======================================")
    print(f"🎉 Account: @{username}")
    print(f"🎉 Caption: Dag {day_number}")
    print(f"🎉 Container: {container_id}")
    print("🎉 =======================================")


except Exception as error:

    print("")
    print("❌ =======================================")
    print("❌ INSTAGRAM AUTOMATION FAILED")
    print("❌ =======================================")
    print(f"❌ Error: {error}")
    print("")

    traceback.print_exc()

    sys.exit(1)
