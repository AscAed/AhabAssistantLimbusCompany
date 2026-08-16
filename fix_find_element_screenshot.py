import re

with open('tasks/event/event_handling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure event_handling.py is updated
if 'take_screenshot=False' not in content:
    content = content.replace(
        'for level in ["very_high", "high", "normal", "low", "very_low"]:',
        '# ⚡ Bolt: Capture screen once outside the loop instead of capturing up to 5 times sequentially\n        auto.take_screenshot()\n        for level in ["very_high", "high", "normal", "low", "very_low"]:'
    )
    content = content.replace(
        'if best_option := auto.find_element(f"event/{level}.png"):',
        'if best_option := auto.find_element(f"event/{level}.png", take_screenshot=False):'
    )

with open('tasks/event/event_handling.py', 'w', encoding='utf-8') as f:
    f.write(content)
