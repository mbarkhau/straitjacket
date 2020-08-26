#!/bin/bash
AUTHOR_NAME="Manuel Barkhau"
AUTHOR_EMAIL="mbarkhau@gmail.com"

KEYWORDS="formatter yapf black pyfmt gofmt"
DESCRIPTION="Another Uncompromising Code Formatter for Python."

LICENSE_ID="MIT"

PACKAGE_NAME="straitjacket"
MODULE_NAME="straitjacket"
GIT_REPO_NAMESPACE="mbarkhau"
GIT_REPO_DOMAIN="gitlab.com"

PACKAGE_VERSION="v202008.1015"

DEFAULT_PYTHON_VERSION="python=3.6"
SUPPORTED_PYTHON_VERSIONS="python=3.6 python=3.7"

IS_PUBLIC=1


# PAGES_URL="https://${NAMESPACE}.${PAGES_DOMAIN}/${PACKAGE_NAME}/"

## Download and run the actual update script

if [[ $KEYWORDS == "keywords used on pypi" ]]; then
    echo "FAILSAFE! Default bootstrapit config detected.";
    echo "Did you forget to update parameters in your 'bootstrapit.sh' ?"
    exit 1;
fi

PROJECT_DIR=$(dirname "$0");

if ! [[ -f "$PROJECT_DIR/scripts/bootstrapit_update.sh" ]]; then
    mkdir -p "$PROJECT_DIR/scripts/";
    RAW_FILES_URL="https://gitlab.com/mbarkhau/bootstrapit/raw/master";
    curl --silent "$RAW_FILES_URL/scripts/bootstrapit_update.sh" \
        > "$PROJECT_DIR/scripts/bootstrapit_update.sh.tmp";
    mv "$PROJECT_DIR/scripts/bootstrapit_update.sh.tmp" \
        "$PROJECT_DIR/scripts/bootstrapit_update.sh";
fi

source "$PROJECT_DIR/scripts/bootstrapit_update.sh";
