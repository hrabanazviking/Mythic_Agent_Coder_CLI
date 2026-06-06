from pathlib import Path
import random

def get_image(agent_name):
    agent_name_lower = agent_name.lower()
    if "runa" in agent_name_lower or "primary" in agent_name_lower:
        prefix = "Runa_Gridweaver_Freyasdottir"
    elif "forge" in agent_name_lower:
        prefix = "Forge_Worker"
    elif "thor" in agent_name_lower:
        prefix = "Thor"
    else:
        prefix = agent_name.split("-")[0].strip()
        
    chars_dir = Path("default_agent_characters")
    if not chars_dir.exists():
        print(f"Error: {chars_dir} does not exist.")
        return
        
    matches = []
    for f in chars_dir.glob(f"{prefix}*.*"):
        if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            matches.append(f)
            
    print(f"Prefix: {prefix}, Matches: {matches}")

get_image("Thor Guardian")
