#!/usr/bin/env bash
set -euo pipefail
bad='(AIza|ghp_|github_pat_|BEGIN (RSA |OPENSSH )?PRIVATE KEY)'
if rg -n -i --glob '!scripts/public_safety_check.sh' "$bad" .; then
  echo "Проверка не пройдена: в публикуемых файлах найдено выражение, похожее на секрет."
  exit 1
fi
echo "Проверка публикации пройдена: признаки секретов не найдены."
