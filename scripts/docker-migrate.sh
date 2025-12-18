#!/bin/bash
# Run database migrations in docker container

set -e

CONTAINER_NAME="ragagent-backend"

show_menu() {
    echo ""
    echo "=== Docker Migration Menu ==="
    echo "1) Run migrations (upgrade head)"
    echo "2) Create new migration"
    echo "3) Rollback one migration"
    echo "4) Reset to base"
    echo "5) Show current revision"
    echo "6) Show migration history"
    echo "0) Exit"
    echo ""
    read -p "Select option: " choice
}

run_migrate() {
    echo "Running migrations..."
    docker exec $CONTAINER_NAME uv run alembic upgrade head
}

create_migration() {
    read -p "Enter migration name: " name
    if [ -z "$name" ]; then
        echo "Error: Migration name is required"
        return
    fi
    echo "Creating migration: $name"
    docker exec $CONTAINER_NAME uv run alembic revision --autogenerate -m "$name"
}

rollback() {
    echo "Rolling back one migration..."
    docker exec $CONTAINER_NAME uv run alembic downgrade -1
}

reset_db() {
    read -p "Are you sure? This will reset all migrations (y/N): " confirm
    if [ "$confirm" == "y" ] || [ "$confirm" == "Y" ]; then
        echo "Resetting database to base..."
        docker exec $CONTAINER_NAME uv run alembic downgrade base
    else
        echo "Cancelled"
    fi
}

show_current() {
    echo "Current revision:"
    docker exec $CONTAINER_NAME uv run alembic current
}

show_history() {
    echo "Migration history:"
    docker exec $CONTAINER_NAME uv run alembic history
}

# Handle command line arguments
if [ -n "$1" ]; then
    case "$1" in
        up|upgrade)
            run_migrate
            ;;
        create)
            if [ -z "$2" ]; then
                echo "Usage: ./scripts/docker-migrate.sh create <migration_name>"
                exit 1
            fi
            echo "Creating migration: $2"
            docker exec $CONTAINER_NAME uv run alembic revision --autogenerate -m "$2"
            ;;
        down)
            rollback
            ;;
        reset)
            reset_db
            ;;
        current)
            show_current
            ;;
        history)
            show_history
            ;;
        *)
            echo "Unknown command: $1"
            echo "Usage: ./scripts/docker-migrate.sh [up|create|down|reset|current|history]"
            exit 1
            ;;
    esac
    exit 0
fi

# Interactive menu
while true; do
    show_menu
    case $choice in
        1) run_migrate ;;
        2) create_migration ;;
        3) rollback ;;
        4) reset_db ;;
        5) show_current ;;
        6) show_history ;;
        0) echo "Bye!"; exit 0 ;;
        *) echo "Invalid option" ;;
    esac
done
