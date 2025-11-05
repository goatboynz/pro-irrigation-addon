#!/usr/bin/env bash
set -e

echo "============================================================"
echo "Pro-Irrigation Add-on - Build Script"
echo "============================================================"

# Default values
PLATFORM="${PLATFORM:-linux/amd64}"
TAG="${TAG:-pro-irrigation:latest}"
NO_CACHE="${NO_CACHE:-false}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="true"
            shift
            ;;
        --help)
            echo "Usage: ./build.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --platform PLATFORM    Target platform (default: linux/amd64)"
            echo "                         Examples: linux/amd64, linux/arm64, linux/arm/v7"
            echo "  --tag TAG             Docker image tag (default: pro-irrigation:latest)"
            echo "  --no-cache            Build without using cache"
            echo "  --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./build.sh"
            echo "  ./build.sh --platform linux/arm64 --tag pro-irrigation:arm64"
            echo "  ./build.sh --no-cache"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Build Configuration:"
echo "  Platform: $PLATFORM"
echo "  Tag: $TAG"
echo "  No Cache: $NO_CACHE"
echo "============================================================"

# Build command
BUILD_CMD="docker build"

if [ "$NO_CACHE" = "true" ]; then
    BUILD_CMD="$BUILD_CMD --no-cache"
fi

BUILD_CMD="$BUILD_CMD --platform $PLATFORM -t $TAG ."

echo "Running: $BUILD_CMD"
echo "============================================================"

# Execute build
eval $BUILD_CMD

echo "============================================================"
echo "Build completed successfully!"
echo "Image: $TAG"
echo ""
echo "To run the container locally:"
echo "  docker run -p 8000:8000 -v \$(pwd)/data:/data $TAG"
echo ""
echo "To test the add-on in Home Assistant:"
echo "  1. Copy the entire directory to /addons/pro-irrigation/"
echo "  2. Restart Home Assistant"
echo "  3. Install the add-on from the Add-on Store"
echo "============================================================"
