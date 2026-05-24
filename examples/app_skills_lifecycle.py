"""App Skills closed-loop learning lifecycle demo."""

from cua_harness import (
    ensure_daemon,
    launch_app,
    get_window_state,
    click,
    type_text,
    press_key,
    save_app_skill,
    load_app_skills,
)

BUNDLE = "com.apple.Notes"

ensure_daemon()

# Step 1: Launch Notes
result = launch_app(bundle_id=BUNDLE)
pid = result["pid"]
print(f"Notes launched, pid={pid}")

# Step 2: Check if app-skills already exist
state = get_window_state(pid, capture_mode="som")

if state.get("app_skills"):
    print(f"Skills already learned: {state['app_skills']}")
    # Step 6: Load and call existing skills
    ns = {}
    load_app_skills(BUNDLE, ns)
    ns["create_note"](pid, "Hello from app-skills!")
    print("Called create_note via learned skill")
else:
    print("No skills yet — performing manual exploration...")

    # Step 3: Manual operation — create a note
    click(pid, element_index=0)  # click "New Note" button
    type_text(pid, "First automated note")
    press_key(pid, "Return")
    print("Manual note created successfully")

    # Step 4: Encode the successful path as an app-skill
    save_app_skill(BUNDLE, """
from cua_harness import get_window_state, click, type_text, press_key

def create_note(pid, content):
    state = get_window_state(pid, capture_mode='som')
    click(pid, element_index=0)
    type_text(pid, content)
    press_key(pid, "Return")
""", reason="learned New Note button path via element_index=0")
    print("App-skill saved")

    # Step 5: Verify next get_window_state returns app_skills path
    state = get_window_state(pid, capture_mode="som")
    assert state.get("app_skills"), "Expected app_skills path in state"
    print(f"Verified: app_skills path = {state['app_skills']}")

    # Step 6: Load and call the just-saved skill
    ns = {}
    load_app_skills(BUNDLE, ns)
    ns["create_note"](pid, "Second note via learned skill")
    print("Closed loop complete: save → load → call")
