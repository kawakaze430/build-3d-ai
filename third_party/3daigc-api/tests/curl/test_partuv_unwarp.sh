#!/bin/bash

##############################################################################
# PartUV UV Unwrapping Test Script
# 
# This script tests the PartUV UV unwrapping endpoint with automatic
# job status polling and result download.
#
# Usage:
#   ./test_partuv_unwrap.sh [mesh_file] [variant]
#
# Arguments:
#   mesh_file  - Path to input mesh file (default: uses example mesh)
#   variant    - Packing method: 'blender', 'none', or 'uvpackmaster' (default: blender)
#
# Example:
#   ./test_partuv_unwrap.sh assets/example_mesh/typical_creature_furry.obj blender
#   ./test_partuv_unwrap.sh my_mesh.obj none
##############################################################################

set -e  # Exit on error

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:7842/api/v1}"
POLL_INTERVAL=5  # seconds
MAX_WAIT_TIME=600  # 10 minutes
OUTPUT_DIR="./test_outputs/partuv_unwrap"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    log_error "jq is required but not installed. Please install it:"
    log_error "  macOS: brew install jq"
    log_error "  Ubuntu/Debian: apt-get install jq"
    exit 1
fi

# Parse arguments
MESH_FILE="${1:-assets/example_uv/max-planck.obj}"
PACK_METHOD="${2:-blender}"

# Validate pack method
if [[ ! "$PACK_METHOD" =~ ^(blender|none|uvpackmaster)$ ]]; then
    log_error "Invalid pack method: $PACK_METHOD"
    log_error "Valid options: blender, none, uvpackmaster"
    exit 1
fi

# Check if mesh file exists
if [ ! -f "$MESH_FILE" ]; then
    log_error "Mesh file not found: $MESH_FILE"
    log_error "Please provide a valid mesh file path"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

log_info "=========================================="
log_info "PartUV UV Unwrapping Test"
log_info "=========================================="
log_info "Input mesh: $MESH_FILE"
log_info "Pack method: $PACK_METHOD"
log_info "Output directory: $OUTPUT_DIR"
log_info "=========================================="

# Step 1: Check available models
log_info "Step 1: Checking available UV unwrapping models..."
MODELS_RESPONSE=$(curl -s "${API_BASE_URL}/mesh-uv-unwrapping/available-models")
echo "$MODELS_RESPONSE" | jq '.'
log_success "Available models retrieved"

# Step 2: Check supported formats
log_info "Step 2: Checking supported formats..."
FORMATS_RESPONSE=$(curl -s "${API_BASE_URL}/mesh-uv-unwrapping/supported-formats")
echo "$FORMATS_RESPONSE" | jq '.'
log_success "Supported formats retrieved"

# Step 3: Check packing methods
log_info "Step 3: Checking packing methods..."
PACK_METHODS_RESPONSE=$(curl -s "${API_BASE_URL}/mesh-uv-unwrapping/pack-methods")
echo "$PACK_METHODS_RESPONSE" | jq '.'
log_success "Packing methods retrieved"

# Step 4: Upload mesh file
log_info "Step 4: Uploading mesh file..."
UPLOAD_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/file-upload/mesh" \
    -F "file=@${MESH_FILE}")

# Check if upload was successful
if [ -z "$UPLOAD_RESPONSE" ]; then
    log_error "Upload failed - no response from server"
    exit 1
fi

FILE_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.file_id // empty')
if [ -z "$FILE_ID" ]; then
    log_error "Upload failed - could not get file_id"
    echo "$UPLOAD_RESPONSE" | jq '.'
    exit 1
fi

log_success "Mesh uploaded successfully. File ID: $FILE_ID"

# Step 5: Submit UV unwrapping job
log_info "Step 5: Submitting UV unwrapping job..."
JOB_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/mesh-uv-unwrapping/unwrap-mesh" \
    -H "Content-Type: application/json" \
    -d "{
        \"mesh_file_id\": \"${FILE_ID}\",
        \"distortion_threshold\": 1.25,
        \"pack_method\": \"${PACK_METHOD}\",
        \"save_individual_parts\": true,
        \"save_visuals\": false,
        \"output_format\": \"obj\",
        \"model_preference\": \"partuv_uv_unwrapping\"
    }")

# Check if job submission was successful
if [ -z "$JOB_RESPONSE" ]; then
    log_error "Job submission failed - no response from server"
    exit 1
fi

JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id // empty')
if [ -z "$JOB_ID" ]; then
    log_error "Job submission failed - could not get job_id"
    echo "$JOB_RESPONSE" | jq '.'
    exit 1
fi

log_success "Job submitted successfully. Job ID: $JOB_ID"

# Step 6: Poll job status
log_info "Step 6: Polling job status..."
START_TIME=$(date +%s)
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT_TIME ]; do
    STATUS_RESPONSE=$(curl -s "${API_BASE_URL}/system/jobs/${JOB_ID}")
    
    JOB_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status // empty')
    
    if [ -z "$JOB_STATUS" ]; then
        log_error "Failed to get job status"
        echo "$STATUS_RESPONSE" | jq '.'
        exit 1
    fi
    
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    case "$JOB_STATUS" in
        "completed")
            log_success "Job completed! (took ${ELAPSED}s)"
            echo "$STATUS_RESPONSE" | jq '.result'
            
            # Extract result information
            OUTPUT_MESH_PATH=$(echo "$STATUS_RESPONSE" | jq -r '.result.output_mesh_path // empty')
            PACKED_MESH_PATH=$(echo "$STATUS_RESPONSE" | jq -r '.result.packed_mesh_path // empty')
            NUM_COMPONENTS=$(echo "$STATUS_RESPONSE" | jq -r '.result.num_components // 0')
            DISTORTION=$(echo "$STATUS_RESPONSE" | jq -r '.result.distortion // 0')
            
            log_info "UV Unwrapping Results:"
            log_info "  - Output mesh: $OUTPUT_MESH_PATH"
            log_info "  - Packed mesh: $PACKED_MESH_PATH"
            log_info "  - UV components: $NUM_COMPONENTS"
            log_info "  - Final distortion: $DISTORTION"
            
            # Step 7: Download result files
            log_info "Step 7: Downloading result files..."
            
            # Download main mesh with UVs
            OUTPUT_FILE="${OUTPUT_DIR}/mesh_with_uv_${PACK_METHOD}.obj"
            curl -s "${API_BASE_URL}/system/jobs/${JOB_ID}/download" -o "$OUTPUT_FILE"
            
            if [ -f "$OUTPUT_FILE" ]; then
                FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
                log_success "Downloaded UV unwrapped mesh: $OUTPUT_FILE (${FILE_SIZE} bytes)"
            else
                log_error "Failed to download result file"
            fi
            
            # Download generation info
            INFO_FILE="${OUTPUT_DIR}/uv_info_${PACK_METHOD}.json"
            echo "$STATUS_RESPONSE" | jq '.result' > "$INFO_FILE"
            log_success "Saved generation info: $INFO_FILE"
            
            break
            ;;
        "failed")
            log_error "Job failed!"
            ERROR_MSG=$(echo "$STATUS_RESPONSE" | jq -r '.error // "Unknown error"')
            log_error "Error: $ERROR_MSG"
            echo "$STATUS_RESPONSE" | jq '.'
            exit 1
            ;;
        "queued"|"processing")
            printf "\r${YELLOW}[WAITING]${NC} Status: %-12s Elapsed: %3ds / %ds" "$JOB_STATUS" "$ELAPSED" "$MAX_WAIT_TIME"
            sleep $POLL_INTERVAL
            ;;
        *)
            log_warning "Unknown status: $JOB_STATUS"
            sleep $POLL_INTERVAL
            ;;
    esac
done
echo  # New line after progress

if [ $ELAPSED -ge $MAX_WAIT_TIME ]; then
    log_error "Timeout waiting for job completion (${MAX_WAIT_TIME}s)"
    exit 1
fi

log_info "=========================================="
log_success "UV Unwrapping test completed successfully!"
log_info "=========================================="
log_info "Results saved in: $OUTPUT_DIR"
log_info "Job ID: $JOB_ID"

