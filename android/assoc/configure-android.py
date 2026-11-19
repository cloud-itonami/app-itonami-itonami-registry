"""Configure offline permissions and launcher art in the generated Android host."""
from pathlib import Path
import re
from shutil import copytree


tauri = Path(__file__).parent / "src-tauri"
android = tauri / "gen/android/app/src/main"
manifest = android / "AndroidManifest.xml"
source = manifest.read_text()
offline = re.sub(
    r'^ *<uses-permission android:name="android\.permission\.INTERNET"\s*/>\n',
    "",
    source,
    flags=re.MULTILINE,
)
if "android.permission.INTERNET" in offline:
    raise SystemExit("Remove INTERNET from the generated assoc Android manifest")
configured = offline
if 'android:roundIcon=' not in configured:
    configured = configured.replace(
        'android:icon="@mipmap/ic_launcher"',
        'android:icon="@mipmap/ic_launcher" android:roundIcon="@mipmap/ic_launcher_round"',
    )
if configured != source:
    manifest.write_text(configured)
copytree(tauri / "icons/android", android / "res", dirs_exist_ok=True)
