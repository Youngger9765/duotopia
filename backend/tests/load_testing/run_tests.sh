#!/bin/bash
# Load Testing Execution Script
# Runs various load test scenarios against different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="staging"
SCENARIO="normal"
WEB_UI="false"
HEADLESS="false"

# Function to print usage
print_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -e, --env       Environment (staging|production|local) [default: staging]"
    echo "  -s, --scenario  Test scenario (normal|peak|stress|spike|endurance|breaking) [default: normal]"
    echo "  -u, --users     Number of users [default: from scenario]"
    echo "  -r, --rate      Spawn rate (users/second) [default: from scenario]"
    echo "  -t, --time      Test duration [default: from scenario]"
    echo "  -w, --web       Enable web UI (port 8089)"
    echo "  --headless      Run headless (no web UI, print stats to console)"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Run normal load test against staging with web UI"
    echo "  $0 --env staging --scenario normal --web"
    echo ""
    echo "  # Run stress test against production (headless)"
    echo "  $0 --env production --scenario stress --headless"
    echo ""
    echo "  # Custom test: 50 users, 5 users/sec, 10 minutes"
    echo "  $0 --env staging --users 50 --rate 5 --time 10m --web"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--scenario)
            SCENARIO="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        -w|--web)
            WEB_UI="true"
            shift
            ;;
        --headless)
            HEADLESS="true"
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Set scenario-specific defaults if not overridden
case $SCENARIO in
    normal)
        USERS="${USERS:-20}"
        SPAWN_RATE="${SPAWN_RATE:-2}"
        RUN_TIME="${RUN_TIME:-5m}"
        ;;
    peak)
        USERS="${USERS:-50}"
        SPAWN_RATE="${SPAWN_RATE:-5}"
        RUN_TIME="${RUN_TIME:-5m}"
        ;;
    stress)
        USERS="${USERS:-100}"
        SPAWN_RATE="${SPAWN_RATE:-10}"
        RUN_TIME="${RUN_TIME:-10m}"
        ;;
    spike)
        USERS="${USERS:-50}"
        SPAWN_RATE="${SPAWN_RATE:-50}"
        RUN_TIME="${RUN_TIME:-3m}"
        ;;
    endurance)
        USERS="${USERS:-30}"
        SPAWN_RATE="${SPAWN_RATE:-3}"
        RUN_TIME="${RUN_TIME:-30m}"
        ;;
    breaking)
        USERS="${USERS:-200}"
        SPAWN_RATE="${SPAWN_RATE:-20}"
        RUN_TIME="${RUN_TIME:-10m}"
        ;;
    *)
        echo -e "${RED}❌ Unknown scenario: $SCENARIO${NC}"
        print_usage
        exit 1
        ;;
esac

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production|local)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Must be one of: staging, production, local"
    exit 1
fi

# Warning for production tests
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}⚠️  WARNING: You are about to load test PRODUCTION!${NC}"
    echo "This will impact real users and create real data."
    echo ""
    read -p "Are you absolutely sure? Type 'YES' to continue: " confirm
    if [ "$confirm" != "YES" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# Print test configuration
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Duotopia Load Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Environment:  $ENVIRONMENT"
echo "Scenario:     $SCENARIO"
echo "Users:        $USERS"
echo "Spawn Rate:   $SPAWN_RATE users/sec"
echo "Duration:     $RUN_TIME"
echo "Web UI:       $WEB_UI"
echo "Headless:     $HEADLESS"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create results directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results/${ENVIRONMENT}_${SCENARIO}_${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

# Export environment variables
export TEST_ENV="$ENVIRONMENT"
export RESULTS_DIR

# Check if .env file exists
if [ -f "../../../.env.$ENVIRONMENT" ]; then
    echo -e "${GREEN}✅ Loading credentials from .env.$ENVIRONMENT${NC}"
    set -a
    source "../../../.env.$ENVIRONMENT"
    set +a
else
    echo -e "${YELLOW}⚠️  No .env.$ENVIRONMENT file found, using defaults${NC}"
fi

# Construct Locust command
LOCUST_CMD="locust -f locustfile.py"

# Add user class based on scenario
if [ "$SCENARIO" = "spike" ]; then
    LOCUST_CMD="$LOCUST_CMD --class-picker"
fi

# Add execution mode
if [ "$HEADLESS" = "true" ]; then
    LOCUST_CMD="$LOCUST_CMD --headless"
    LOCUST_CMD="$LOCUST_CMD --users $USERS"
    LOCUST_CMD="$LOCUST_CMD --spawn-rate $SPAWN_RATE"
    LOCUST_CMD="$LOCUST_CMD --run-time $RUN_TIME"
    LOCUST_CMD="$LOCUST_CMD --html $RESULTS_DIR/report.html"
    LOCUST_CMD="$LOCUST_CMD --csv $RESULTS_DIR/results"

    echo -e "${GREEN}🚀 Starting load test (headless mode)...${NC}"
    echo ""

    # Run Locust
    eval $LOCUST_CMD

    echo ""
    echo -e "${GREEN}✅ Test complete! Results saved to: $RESULTS_DIR${NC}"

elif [ "$WEB_UI" = "true" ]; then
    echo -e "${GREEN}🌐 Starting Locust web UI on http://localhost:8089${NC}"
    echo "Configure test parameters in the web interface"
    echo ""

    # Run Locust with web UI
    eval $LOCUST_CMD

else
    echo -e "${RED}❌ Error: Must specify either --web or --headless${NC}"
    print_usage
    exit 1
fi

# Generate summary report
if [ -f "$RESULTS_DIR/results_stats.csv" ]; then
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Test Summary${NC}"
    echo -e "${BLUE}========================================${NC}"

    # Extract key metrics from CSV
    tail -n 1 "$RESULTS_DIR/results_stats.csv" | awk -F',' '{
        printf "Request Count: %s\n", $3
        printf "Failure Count: %s\n", $4
        printf "Median (ms):   %s\n", $5
        printf "95th %ile (ms): %s\n", $7
        printf "Avg (ms):      %s\n", $8
        printf "RPS:           %s\n", $11
    }'

    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Full report: $RESULTS_DIR/report.html"
fi
