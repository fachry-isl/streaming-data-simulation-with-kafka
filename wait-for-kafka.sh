#!/bin/bash
# wait-for-kafka.sh

host="$1"
port="$2"
shift 2
cmd="$@"

# Check if `nc` command is available
if ! command -v nc >/dev/null 2>&1; then
  echo "[ERROR] 'nc' (netcat) is not installed in the container. Exiting."
  exit 1
fi

echo "Waiting for Kafka at $host:$port..."

until nc -z "$host" "$port"; do
  echo "Kafka is unavailable - sleeping"
  sleep 2
done

echo "Kafka is up - executing command"
exec $cmd
