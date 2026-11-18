"""Keep the generated Tauri Android host offline."""
from pathlib import Path
import re


manifest = Path(__file__).parent / "src-tauri/gen/android/app/src/main/AndroidManifest.xml"
source = manifest.read_text()
offline = re.sub(
    r'^ *<uses-permission android:name="android\.permission\.INTERNET"\s*/>\n',
    "",
    source,
    flags=re.MULTILINE,
)
if "android.permission.INTERNET" in offline:
    raise SystemExit("Remove INTERNET from the generated assoc Android manifest")
if offline != source:
    manifest.write_text(offline)
