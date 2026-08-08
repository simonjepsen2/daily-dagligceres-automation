import os
import sys
import traceback

from composio import Composio, App


print("🚀 Starting DagligCeres Instagram post...")


# ============================================================
# COMPOSIO API KEY
# ============================================================

api_key = os.environ.get("COMPOSIO_API_KEY")

if not api_key:
    print("❌ COMPOSIO_API_KEY is missing.")
    print("Make sure it exists under:")
    print("GitHub → Settings → Secrets and variables → Actions")
    sys.exit(1)


# ============================================================
# CONNECT TO COMPOSIO
# ============================================================

composio = Composio(api_key=api_key)


try:

    # ========================================================
    # INSTAGRAM
    # ========================================================

    print("📱 Loading Instagram tools...")

    instagram_tools = composio.get_tools(
        apps=[App.INSTAGRAM]
    )

    print("Available Instagram tools:")

    for tool in instagram_tools:
        print(f"  - {tool.name}")


    # ========================================================
    # GET INSTAGRAM ACCOUNT
    # ========================================================

    print("📊 Getting Instagram account information...")

    user_info_tool = next(
        tool
        for tool in instagram_tools
        if tool.name == "INSTAGRAM_GET_USER_INFO"
    )

    user_info_result = user_info_tool.execute({
        "ig_user_id": "me"
    })

    print(f"Instagram response: {user_info_result}")

    ig_user_id = user_info_result["id"]

    username = user_info_result.get(
        "username",
        "Unknown"
    )

    media_count = user_info_result.get(
        "media_count",
        0
    )

    day_number = media_count + 1

    print(f"👤 Account: @{username}")
    print(f"📅 Posting: Dag {day_number}")


    # ========================================================
    # GOOGLE DRIVE
    # ========================================================

    print("☁️ Loading Google Drive tools...")

    drive_tools = composio.get_tools(
        apps=[App.GOOGLEDRIVE]
    )

    print("Available Google Drive tools:")

    for tool in drive_tools:
        print(f"  - {tool.name}")


    download_tool = next(
        tool
        for tool in drive_tools
        if tool.name == "GOOGLEDRIVE_DOWNLOAD_FILE"
    )


    print("⬇️ Downloading DagligCeres image...")


    download_result = download_tool.execute({
        "fileId": "1FpB9exKU8IuOeUqQjgdg56fNFZy-Ty4E"
    })


    print("Google Drive response received.")


    image_url = (
        download_result[
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


    create_media_tool = next(
        tool
        for tool in instagram_tools
        if tool.name == "INSTAGRAM_POST_IG_USER_MEDIA"
    )


    container_result = create_media_tool.execute({

        "ig_user_id": ig_user_id,

        "image_url": image_url,

        "caption": f"Dag {day_number}"

    })


    print(
        f"Container response: {container_result}"
    )


    container_id = container_result["id"]


    print(
        f"✅ Instagram container created: "
        f"{container_id}"
    )


    # ========================================================
    # PUBLISH TO INSTAGRAM
    # ========================================================

    print("🚀 Publishing to Instagram...")


    publish_tool = next(
        tool
        for tool in instagram_tools
        if tool.name ==
        "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH"
    )


    publish_result = publish_tool.execute({

        "ig_user_id": ig_user_id,

        "creation_id": container_id,

        "max_wait_seconds": 120

    })


    print(
        f"Publish response: {publish_result}"
    )


    media_id = publish_result.get("id")


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
    
