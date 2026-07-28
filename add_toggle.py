import glob
import re

button_html = """      <!-- Dark Mode Toggle Button -->
      <button onclick="toggleDarkMode()" aria-label="Toggle theme" class="material-symbols-outlined p-2 text-on-surface-variant dark:text-primary-fixed-dim hover:bg-surface-container-high dark:hover:bg-primary-container rounded-full transition-colors active:scale-95">
        dark_mode
      </button>"""

for filepath in glob.glob("*.html"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "toggleDarkMode()" in content:
        print(f"Skipped (already exists): {filepath}")
        continue

    # Look for notifications button OR header action container
    pattern = re.compile(
        r"(<button[^>]*aria-label=[\"\']Notifications[\"\'][^>]*>|<div[^>]*class=[\"\'][^\"\']*flex[^\"\']*items-center[^\"\']*gap-md[^\"\']*[\"\'][^>]*>)",
        re.IGNORECASE
    )

    if pattern.search(content):
        new_content = pattern.sub(rf"\n{button_html}\n\1", content, count=1)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Successfully added toggle to: {filepath}")
    else:
        print(f"Could not locate target header area in: {filepath}")
