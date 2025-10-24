#!/usr/bin/env python3
"""
start_basics.py

This script starts only the basic services needed for development:
- Supabase (full stack)
- PostgreSQL
- n8n
- Neo4j
- SearXNG

Both stacks use the same Docker Compose project name ("localai")
so they appear together in Docker Desktop.
"""

import os
import subprocess
import shutil
import time
import argparse
import platform

def run_command(cmd, cwd=None):
    """Run a shell command and print it."""
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)

def clone_supabase_repo():
    """Clone the Supabase repository using sparse checkout if not already present."""
    if not os.path.exists("supabase"):
        print("Cloning the Supabase repository...")
        run_command([
            "git", "clone", "--filter=blob:none", "--no-checkout",
            "https://github.com/supabase/supabase.git"
        ])
        os.chdir("supabase")
        run_command(["git", "sparse-checkout", "init", "--cone"])
        run_command(["git", "sparse-checkout", "set", "docker"])
        run_command(["git", "checkout", "master"])
        os.chdir("..")
    else:
        print("Supabase repository already exists, updating...")
        os.chdir("supabase")
        # Check if there are local changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("Local changes detected, stashing them...")
            run_command(["git", "stash"])
            run_command(["git", "pull", "--rebase=false"])
            print("Attempting to reapply stashed changes...")
            try:
                run_command(["git", "stash", "pop"])
            except subprocess.CalledProcessError:
                print("Warning: Could not automatically reapply stashed changes.")
                print("Your changes are saved in the stash. Use 'git stash list' to view them.")
        else:
            run_command(["git", "pull", "--rebase=false"])
        os.chdir("..")

def prepare_supabase_env():
    """Copy .env to .env in supabase/docker."""
    env_path = os.path.join("supabase", "docker", ".env")
    env_example_path = os.path.join(".env")
    print("Copying .env in root to .env in supabase/docker...")
    shutil.copyfile(env_example_path, env_path)

def stop_existing_containers():
    """Stop and remove existing containers for the basic services."""
    print("Stopping existing basic service containers...")

    # Stop Supabase stack
    try:
        run_command(["docker", "compose", "-p", "localai", "-f", "supabase/docker/docker-compose.yml", "down"])
    except subprocess.CalledProcessError:
        print("No Supabase containers to stop or error occurred.")

    # Stop only the basic services from the main stack
    basic_services = ["postgres", "n8n", "neo4j", "searxng"]
    for service in basic_services:
        try:
            cmd = ["docker", "compose", "-p", "localai", "-f", "docker-compose.yml"]
            cmd.extend(["-f", "docker-compose.override.private.yml"])
            cmd.extend(["stop", service])
            run_command(cmd)
        except subprocess.CalledProcessError:
            print(f"No {service} container to stop or error occurred.")

def start_supabase(environment=None, retries=3):
    """Start the Supabase services (using its compose file)."""
    print("Starting Supabase services...")
    cmd = ["docker", "compose", "-p", "localai", "-f", "supabase/docker/docker-compose.yml"]
    if environment and environment == "public":
        cmd.extend(["-f", "docker-compose.override.public.supabase.yml"])
    cmd.extend(["up", "-d"])

    # Retry logic for network issues
    for attempt in range(retries):
        try:
            run_command(cmd)
            return  # Success, exit the function
        except subprocess.CalledProcessError:
            if attempt < retries - 1:
                print(f"\nAttempt {attempt + 1} failed. Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"\nFailed after {retries} attempts.")
                raise

def start_basic_services(environment=None, retries=3):
    """Start only the basic services: postgres, n8n, neo4j, searxng."""
    print("Starting basic services (postgres, n8n, neo4j, searxng)...")

    # List of services to start
    basic_services = ["postgres", "n8n", "neo4j", "searxng"]

    cmd = ["docker", "compose", "-p", "localai", "-f", "docker-compose.yml"]
    if environment and environment == "private":
        cmd.extend(["-f", "docker-compose.override.private.yml"])
    if environment and environment == "public":
        cmd.extend(["-f", "docker-compose.override.public.yml"])
    cmd.extend(["up", "-d"] + basic_services)

    # Retry logic for network issues
    for attempt in range(retries):
        try:
            run_command(cmd)
            return  # Success, exit the function
        except subprocess.CalledProcessError:
            if attempt < retries - 1:
                print(f"\nAttempt {attempt + 1} failed. Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"\nFailed after {retries} attempts.")
                raise

def generate_searxng_secret_key():
    """Generate a secret key for SearXNG based on the current platform."""
    print("Checking SearXNG settings...")

    # Define paths for SearXNG settings files
    settings_path = os.path.join("searxng", "settings.yml")
    settings_base_path = os.path.join("searxng", "settings-base.yml")

    # Check if settings-base.yml exists
    if not os.path.exists(settings_base_path):
        print(f"Warning: SearXNG base settings file not found at {settings_base_path}")
        return

    # Check if settings.yml exists, if not create it from settings-base.yml
    if not os.path.exists(settings_path):
        print(f"SearXNG settings.yml not found. Creating from {settings_base_path}...")
        try:
            shutil.copyfile(settings_base_path, settings_path)
            print(f"Created {settings_path} from {settings_base_path}")
        except Exception as e:
            print(f"Error creating settings.yml: {e}")
            return
    else:
        print(f"SearXNG settings.yml already exists at {settings_path}")

    # Check if secret key needs to be generated (if file contains 'ultrasecretkey')
    try:
        with open(settings_path, 'r') as f:
            content = f.read()

        if 'ultrasecretkey' not in content:
            print("SearXNG secret key already configured.")
            return

        print("Generating SearXNG secret key...")

        # Generate random key using openssl
        openssl_cmd = ["openssl", "rand", "-hex", "32"]
        random_key = subprocess.check_output(openssl_cmd).decode('utf-8').strip()

        # Replace the key in memory
        updated_content = content.replace('ultrasecretkey', random_key)

        # Write back to file with proper permissions
        with open(settings_path, 'w') as f:
            f.write(updated_content)

        print(f"SearXNG secret key generated successfully: {random_key[:16]}...")

    except Exception as e:
        print(f"Error generating SearXNG secret key: {e}")
        print("You may need to manually generate the secret key using the commands:")
        print("  - Linux: sed -i \"s|ultrasecretkey|$(openssl rand -hex 32)|g\" searxng/settings.yml")
        print("  - macOS: sed -i '' \"s|ultrasecretkey|$(openssl rand -hex 32)|g\" searxng/settings.yml")

def check_and_fix_docker_compose_for_searxng():
    """Check and modify docker-compose.yml for SearXNG first run."""
    docker_compose_path = "docker-compose.yml"
    if not os.path.exists(docker_compose_path):
        print(f"Warning: Docker Compose file not found at {docker_compose_path}")
        return

    try:
        # Read the docker-compose.yml file
        with open(docker_compose_path, 'r') as file:
            content = file.read()

        # Default to first run
        is_first_run = True

        # Check if Docker is running and if the SearXNG container exists
        try:
            # Check if the SearXNG container is running
            container_check = subprocess.run(
                ["docker", "ps", "--filter", "name=searxng", "--format", "{{.Names}}"],
                capture_output=True, text=True, check=True
            )
            searxng_containers = container_check.stdout.strip().split('\n')

            # If SearXNG container is running, check inside for uwsgi.ini
            if any(container for container in searxng_containers if container):
                container_name = next(container for container in searxng_containers if container)
                print(f"Found running SearXNG container: {container_name}")

                # Check if uwsgi.ini exists inside the container
                container_check = subprocess.run(
                    ["docker", "exec", container_name, "sh", "-c", "[ -f /etc/searxng/uwsgi.ini ] && echo 'found' || echo 'not_found'"],
                    capture_output=True, text=True, check=False
                )

                if "found" in container_check.stdout:
                    print("Found uwsgi.ini inside the SearXNG container - not first run")
                    is_first_run = False
                else:
                    print("uwsgi.ini not found inside the SearXNG container - first run")
                    is_first_run = True
            else:
                print("No running SearXNG container found - assuming first run")
        except Exception as e:
            print(f"Error checking Docker container: {e} - assuming first run")

        if is_first_run and "cap_drop: - ALL" in content:
            print("First run detected for SearXNG. Temporarily removing 'cap_drop: - ALL' directive...")
            # Temporarily comment out the cap_drop line
            modified_content = content.replace("cap_drop: - ALL", "# cap_drop: - ALL  # Temporarily commented out for first run")

            # Write the modified content back
            with open(docker_compose_path, 'w') as file:
                file.write(modified_content)

            print("Note: After the first run completes successfully, you should re-add 'cap_drop: - ALL' to docker-compose.yml for security reasons.")
        elif not is_first_run and "# cap_drop: - ALL  # Temporarily commented out for first run" in content:
            print("SearXNG has been initialized. Re-enabling 'cap_drop: - ALL' directive for security...")
            # Uncomment the cap_drop line
            modified_content = content.replace("# cap_drop: - ALL  # Temporarily commented out for first run", "cap_drop: - ALL")

            # Write the modified content back
            with open(docker_compose_path, 'w') as file:
                file.write(modified_content)

    except Exception as e:
        print(f"Error checking/modifying docker-compose.yml for SearXNG: {e}")

def main():
    parser = argparse.ArgumentParser(description='Start only basic services: Supabase, PostgreSQL, n8n, Neo4j, and SearXNG.')
    parser.add_argument('--environment', choices=['private', 'public'], default='private',
                      help='Environment to use for Docker Compose (default: private)')
    args = parser.parse_args()

    clone_supabase_repo()
    prepare_supabase_env()

    # Generate SearXNG secret key and check docker-compose.yml
    generate_searxng_secret_key()
    check_and_fix_docker_compose_for_searxng()

    # Stop existing containers (only the ones we're managing)
    stop_existing_containers()

    # Start Supabase first
    start_supabase(args.environment)

    # Give Supabase some time to initialize
    print("Waiting for Supabase to initialize...")
    time.sleep(10)

    # Then start the basic services
    start_basic_services(args.environment)

    print("\n" + "="*60)
    print("Basic services started successfully!")
    print("="*60)
    print("\nRunning services:")
    print("  - Supabase Studio:  http://localhost:54323")
    print("  - PostgreSQL:       localhost:5435")
    print("  - n8n:              http://localhost:5678")
    print("  - Neo4j Browser:    http://localhost:7474")
    print("  - SearXNG:          http://localhost:8081")
    print("="*60)

if __name__ == "__main__":
    main()
