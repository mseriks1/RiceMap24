#!/usr/bin/env python3
"""Small staging/production smoke check for RiceMap24.

Usage:
  python3 check-web.py https://your-staging-url.onrender.com
"""
from __future__ import annotations
import json
import sys
import urllib.request
import urllib.error

base = (sys.argv[1] if len(sys.argv) > 1 else '').rstrip('/')
if not base:
    print('Usage: python3 check-web.py https://your-staging-url')
    sys.exit(2)

paths = ['/', '/list', '/pricing', '/for-cooks', '/admin', '/health', '/api/cuisines', '/api/listings']
failed = 0
for path in paths:
    url = base + path
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            status = r.status
            body = r.read(4096)
        ok = 200 <= status < 300
        print(f'{status} {path}')
        if not ok:
            failed += 1
        if path == '/health':
            try:
                data = json.loads(body.decode('utf-8'))
                important = {
                    'version': data.get('version'),
                    'env': data.get('env'),
                    'user_data_outside_code_dir': data.get('user_data_outside_code_dir'),
                    'uploads_dir_writable': data.get('uploads_dir_writable'),
                    'backup_dir_writable': data.get('backup_dir_writable'),
                    'stripe_mode': data.get('stripe_mode'),
                    'email_provider': data.get('email_provider'),
                }
                print(json.dumps(important, indent=2))
            except Exception as exc:
                print(f'Could not parse /health JSON: {exc}')
                failed += 1
    except urllib.error.HTTPError as e:
        print(f'{e.code} {path}')
        failed += 1
    except Exception as e:
        print(f'ERROR {path}: {e}')
        failed += 1

sys.exit(1 if failed else 0)
