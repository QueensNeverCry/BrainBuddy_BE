set -euo pipefail # error 발생시 즉시 종료

# --- 옵션 ------------------------
FORCE=0
DAYS_CA=3650
DAYS_CERT=397

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force|-f) FORCE=1; shift ;;
    --days-ca)  DAYS_CA="${2:?}"; shift 2 ;;
    --days-cert) DAYS_CERT="${2:?}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--force|-f] [--days-ca N] [--days-cert N]"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done
# --------------------------------

# --- 경로 보정 ------------------------
# 스크립트 위치 기준으로 리포지토리 루트로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../.."   # <= 여기서부터 모든 경로는 상대경로
# ------------------------------------

# --- 상대경로 정의 ------------------------
CA_DIR="certs/dev/ca"
SERVER_DIR="certs/dev/server"

CA_CNF="${CA_DIR}/ca.cnf"
SERVER_CNF="${SERVER_DIR}/server.cnf"

CA_KEY="${CA_DIR}/ca.key"
CA_CRT="${CA_DIR}/ca.crt"
CA_SRL="${CA_DIR}/ca.srl"

SERVER_KEY="${SERVER_DIR}/server.key"
SERVER_CSR="${SERVER_DIR}/server.csr"
SERVER_CRT="${SERVER_DIR}/server.crt"
FULLCHAIN_PEM="${SERVER_DIR}/fullchain.pem"
# --------------------------------------

# --- 사전 체크 ------------------------
command -v openssl >/dev/null 2>&1 || { echo "[ERR] openssl not found"; exit 1; }

mkdir -p "${CA_DIR}" "${SERVER_DIR}"

[[ -f "${CA_CNF}" ]] || { echo "[ERR] missing: ${CA_CNF}"; exit 1; }
[[ -f "${SERVER_CNF}" ]] || { echo "[ERR] missing: ${SERVER_CNF}"; exit 1; }
# --------------------------------------

# --- 덮어쓰기 헬퍼 ------------------------
maybe_remove() {
  local path="$1"
  if [[ -f "$path" || -L "$path" ]]; then
    if [[ $FORCE -eq 1 ]]; then
      rm -f "$path"
    else
      echo "[SKIP] exists: $path  (use --force to overwrite)"
      return 1
    fi
  fi
  return 0
}
# --------------------------------------

# ---------------------------
# CA 생성
# ---------------------------
echo "==> Generate CA (key, cert)"
if maybe_remove "${CA_KEY}"; then
  openssl genrsa -out "${CA_KEY}" 4096
  chmod 600 "${CA_KEY}"
fi

if maybe_remove "${CA_CRT}"; then
  openssl req -x509 -new -nodes \
    -key "${CA_KEY}" \
    -days "${DAYS_CA}" -sha256 \
    -out "${CA_CRT}" \
    -config "${CA_CNF}"
fi

# ---------------------------
# 서버 키/CSR
# ---------------------------
echo "==> Generate Server key/CSR"
if maybe_remove "${SERVER_KEY}"; then
  openssl genrsa -out "${SERVER_KEY}" 2048
  chmod 600 "${SERVER_KEY}"
fi

if maybe_remove "${SERVER_CSR}"; then
  openssl req -new \
    -key "${SERVER_KEY}" \
    -out "${SERVER_CSR}" \
    -config "${SERVER_CNF}"
fi

# ---------------------------
# 서버 인증서 서명 (SAN 적용)
# ---------------------------
echo "==> Sign Server certificate (with SAN)"
if maybe_remove "${SERVER_CRT}"; then
  [[ -f "${CA_SRL}" && $FORCE -eq 1 ]] && rm -f "${CA_SRL}"
  openssl x509 -req \
    -in "${SERVER_CSR}" \
    -CA "${CA_CRT}" -CAkey "${CA_KEY}" \
    -CAcreateserial -CAserial "${CA_SRL}" \
    -out "${SERVER_CRT}" \
    -days "${DAYS_CERT}" -sha256 \
    -extfile "${SERVER_CNF}" -extensions v3_server
fi

# ---------------------------
# 풀체인 & 검증
# ---------------------------
echo "==> Create fullchain.pem & verify"
if maybe_remove "${FULLCHAIN_PEM}"; then
  cat "${SERVER_CRT}" "${CA_CRT}" > "${FULLCHAIN_PEM}"
fi

openssl verify -CAfile "${CA_CRT}" "${SERVER_CRT}" || {
  echo "[ERR] verify failed"; exit 1;
}

# ---------------------------
# 요약
# ---------------------------
cat <<EOF

[OK] dev certs generated (relative paths)

CA:
  - ${CA_KEY}
  - ${CA_CRT}

Server:
  - ${SERVER_KEY}
  - ${SERVER_CSR}
  - ${SERVER_CRT}
  - ${FULLCHAIN_PEM}

Tip:
  - 브라우저 경고 없이 사용하려면 CA(${CA_CRT})를 신뢰 저장소에 등록하세요.
  - 기존 파일 덮어쓰려면 --force 사용.

EOF

# chmod +x mkcerts.sh
# mkcerts.sh
# mkcerts.sh --force
