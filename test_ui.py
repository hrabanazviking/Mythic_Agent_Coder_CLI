import asyncio
from mythic_agent.ui.main_app import MythicTUI

async def main():
    app = MythicTUI()
    # We run headlessly for 2 seconds to see if it crashes
    await app.run_async(headless=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("Success")
    except Exception as e:
        print(f"Failed: {e}")
