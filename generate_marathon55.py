import subprocess
import sys

if __name__ == '__main__':
    cmd = [sys.executable, 'generate_marathon_missions.py', '--marathon-id', '55']
    raise SystemExit(subprocess.call(cmd))
