"""Prepare both app configurations from the developer's Google/Firebase files."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from duocards.cloud_account import validate_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True, help='Firebase web configuration plus webClientId')
    parser.add_argument('--desktop-client', type=Path, help='Downloaded OAuth Desktop app client JSON')
    parser.add_argument('--android-config', type=Path, help='Downloaded google-services.json; extracts the web client ID')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.desktop_client:
        client = json.loads(args.desktop_client.read_text())['installed']
        config['desktopClientId'] = client['client_id']
        config['desktopClientSecret'] = client.get('client_secret', '')
    if args.android_config:
        android = json.loads(args.android_config.read_text())
        client = next(item for item in android['client'] if item['client_info']['android_client_info']['package_name'] == 'com.studycard.app')
        config['webClientId'] = next(item['client_id'] for item in client['oauth_client'] if item['client_type'] == 3)
        if config['projectId'] != android['project_info']['project_id']:
            parser.error('Android and desktop must use the same Firebase project.')
    validate_config(config, desktop=True)
    validate_config(config, desktop=False)
    fields = ('projectId', 'apiKey', 'databaseURL', 'webClientId', 'desktopClientId', 'desktopClientSecret')
    desktop = {key: config[key] for key in fields if key in config}
    native = {key: desktop[key] for key in fields[:4]}
    (ROOT / 'duocards/data/firebase_config.json').write_text(json.dumps(desktop, indent=2) + '\n')
    (ROOT / 'android/app/src/main/assets/firebase_config.json').write_text(json.dumps(native, indent=2) + '\n')
    print('Desktop and Android Google/Firebase configuration prepared. No credentials were printed.')


if __name__ == '__main__':
    main()
