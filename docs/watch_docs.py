#!python

import os
import subprocess
import time


def get_file_states(directory):
    """
    Returns a dictionary of file paths and their modification times.
    """
    states = {}
    for root, _, files in os.walk(directory):
        for filename in files:
            # Ignore hidden files, temporary editor files, and this script itself
            # fmt:off
            if (filename.startswith('.') or
              filename.endswith('~') or filename == os.path.basename(__file__)):  # noqa: PTH119
                # fmt:on
                continue

            filepath = os.path.join(root, filename)

            # Avoid watching build directories if they are generated inside docs/
            if '_build' in filepath or 'build' in filepath:
                continue

            try:
                states[filepath] = os.path.getmtime(filepath)  # noqa: PTH204
            except OSError:
                pass
    return states


def main():
    # Determine paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Watch the directory where the script is located (docs/)
    watch_dir = script_dir

    command = ['tox', '-e', 'docs']
    poll_interval = 2  # Seconds

    print(f"Watching '{watch_dir}' for changes...")
    print(f"Project root determined as: '{project_root}'")
    print(f"Command to run: {' '.join(command)}")
    print('Press Ctrl+C to stop.')

    # Initial state
    last_states = get_file_states(watch_dir)

    try:
        while True:
            time.sleep(poll_interval)
            current_states = get_file_states(watch_dir)

            if current_states != last_states:
                print('\n[Change Detected] Running docs build...')

                try:
                    # Run tox from the project root so it finds tox.ini
                    subprocess.run(command, cwd=project_root, check=False)  # noqa: S603
                except FileNotFoundError:
                    print("Error: 'tox' command not found. Please ensure tox is installed.")
                except Exception as e:
                    print(f'An error occurred: {e}')

                print(f"\nWaiting for further changes in '{watch_dir}'...")

                # Update state to the current state
                last_states = get_file_states(watch_dir)

    except KeyboardInterrupt:
        print('\nWatcher stopped.')


if __name__ == '__main__':
    main()
