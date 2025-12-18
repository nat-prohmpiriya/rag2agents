#!/bin/bash
# Generate Base64 string

set -e

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -r, --random <bytes>   Generate random Base64 (default: 32 bytes)"
    echo "  -s, --string <text>    Encode string to Base64"
    echo "  -f, --file <path>      Encode file to Base64"
    echo "  -d, --decode <base64>  Decode Base64 to string"
    echo "  -h, --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 -r 32              # Random 32 bytes -> Base64"
    echo "  $0 -s 'hello world'   # Encode string"
    echo "  $0 -f image.png       # Encode file"
    echo "  $0 -d 'aGVsbG8='      # Decode Base64"
}

if [[ $# -eq 0 ]]; then
    # Default: generate 32 random bytes
    openssl rand -base64 32
    exit 0
fi

case "$1" in
    -r|--random)
        bytes="${2:-32}"
        openssl rand -base64 "$bytes"
        ;;
    -s|--string)
        if [[ -z "$2" ]]; then
            echo "Error: String required"
            exit 1
        fi
        echo -n "$2" | base64
        ;;
    -f|--file)
        if [[ -z "$2" ]]; then
            echo "Error: File path required"
            exit 1
        fi
        if [[ ! -f "$2" ]]; then
            echo "Error: File not found: $2"
            exit 1
        fi
        base64 -i "$2"
        ;;
    -d|--decode)
        if [[ -z "$2" ]]; then
            echo "Error: Base64 string required"
            exit 1
        fi
        echo "$2" | base64 -d
        ;;
    -h|--help)
        usage
        ;;
    *)
        echo "Unknown option: $1"
        usage
        exit 1
        ;;
esac
