#!/bin/bash
set -x
nproc; free -g; df -h / | tail -1; docker info --format "{{.ServerVersion}}"
