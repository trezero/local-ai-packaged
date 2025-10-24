#!/usr/bin/env python3
"""
stop_all.py

This script stops and removes all containers associated with this project.
It handles both the Supabase stack and the local AI stack.
"""

import os
import subprocess
import argparse
import sys


def run_command(cmd, cwd=None, check=False):
    """Run a shell command and print it."""
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
    if result.returncode != 0 and result.stderr:
        print(f"Warning: {result.stderr.strip()}")
    return result


def get_project_name():
    """
    Detect the Docker Compose project name by checking running containers.
    Falls back to deriving it from the current directory name.
    """
    # Try to find the project name from existing containers
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False
    )

    if result.returncode == 0 and result.stdout:
        containers = result.stdout.strip().split('\n')
        # Look for supabase or local-ai-packaged containers
        for container in containers:
            if 'supabase' in container or 'local-ai-packaged' in container:
                # Get the project label from this container
                inspect_result = subprocess.run(
                    ["docker", "inspect", container, "--format",
                     "{{index .Config.Labels \"com.docker.compose.project\"}}"],
                    capture_output=True, text=True, check=False
                )
                if inspect_result.returncode == 0 and inspect_result.stdout.strip():
                    project_name = inspect_result.stdout.strip()
                    print(f"Detected Docker Compose project name: {project_name}")
                    return project_name

    # Fallback: use current directory name
    project_name = os.path.basename(os.getcwd())
    print(f"Using directory-based project name: {project_name}")
    return project_name


def stop_supabase_stack(project_name):
    """Stop and remove Supabase containers."""
    print("\n" + "="*60)
    print("Stopping Supabase stack...")
    print("="*60)

    supabase_compose_path = os.path.join("supabase", "docker", "docker-compose.yml")

    if not os.path.exists(supabase_compose_path):
        print(f"Supabase compose file not found at {supabase_compose_path}")
        print("Skipping Supabase stack...")
        return

    cmd = ["docker", "compose", "-p", project_name, "-f", supabase_compose_path, "down"]
    result = run_command(cmd)

    if result.returncode == 0:
        print("Supabase stack stopped successfully.")
    else:
        print("No Supabase containers to stop or error occurred.")


def stop_local_ai_stack(project_name, profile=None):
    """Stop and remove local AI containers."""
    print("\n" + "="*60)
    print("Stopping local AI stack...")
    print("="*60)

    compose_path = "docker-compose.yml"

    if not os.path.exists(compose_path):
        print(f"Docker Compose file not found at {compose_path}")
        print("Skipping local AI stack...")
        return

    cmd = ["docker", "compose", "-p", project_name]

    # Add profile if specified
    if profile and profile != "none":
        cmd.extend(["--profile", profile])

    cmd.extend(["-f", compose_path, "down"])

    result = run_command(cmd)

    if result.returncode == 0:
        print("Local AI stack stopped successfully.")
    else:
        print("No local AI containers to stop or error occurred.")


def stop_all_localai_containers(project_name):
    """Stop all containers with the project name, regardless of profile."""
    print("\n" + "="*60)
    print(f"Stopping all containers in '{project_name}' project...")
    print("="*60)

    # First, try to stop all profiles
    profiles = ["cpu", "gpu-nvidia", "gpu-amd"]

    for profile in profiles:
        print(f"\nChecking for containers with profile: {profile}")
        cmd = ["docker", "compose", "-p", project_name, "--profile", profile, "-f", "docker-compose.yml", "down"]
        run_command(cmd)

    # Also run without any profile to catch remaining containers
    print("\nStopping containers without specific profiles...")
    cmd = ["docker", "compose", "-p", project_name, "-f", "docker-compose.yml", "down"]
    run_command(cmd)


def list_remaining_containers(project_name):
    """List any remaining containers that might be related to this project."""
    print("\n" + "="*60)
    print("Checking for any remaining containers...")
    print("="*60)

    cmd = ["docker", "ps", "-a", "--filter", f"label=com.docker.compose.project={project_name}",
           "--format", "table {{.Names}}\t{{.Status}}"]
    result = run_command(cmd)

    if result.stdout.strip():
        print("\nRemaining containers:")
        print(result.stdout)
    else:
        print(f"\nNo remaining containers found with project name '{project_name}'.")


def main():
    parser = argparse.ArgumentParser(
        description='Stop all containers associated with the local AI packaged project.'
    )
    parser.add_argument(
        '--profile',
        choices=['cpu', 'gpu-nvidia', 'gpu-amd', 'all', 'none'],
        default='all',
        help='Profile to use for Docker Compose. Use "all" to stop all profiles (default: all)'
    )
    parser.add_argument(
        '--check-remaining',
        action='store_true',
        help='Check for any remaining containers after stopping'
    )

    args = parser.parse_args()

    print("="*60)
    print("STOPPING ALL LOCAL AI PACKAGED SERVICES")
    print("="*60)

    # Detect the project name
    project_name = get_project_name()

    # Stop Supabase stack
    stop_supabase_stack(project_name)

    # Stop local AI stack based on profile argument
    if args.profile == "all":
        stop_all_localai_containers(project_name)
    else:
        stop_local_ai_stack(project_name, args.profile)

    # List remaining containers if requested
    if args.check_remaining:
        list_remaining_containers(project_name)

    print("\n" + "="*60)
    print("ALL SERVICES STOPPED")
    print("="*60)
    print("\nAll containers associated with this project have been stopped.")
    print("To start services again, use:")
    print("  - start_basics.py   (for basic services only)")
    print("  - start_services.py (for all services)")
    print("="*60)


if __name__ == "__main__":
    main()
