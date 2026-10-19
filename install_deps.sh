#!/bin/bash
# ============================================================
#  ChacalitosTCG - Script de Instalación de Dependencias
#  Compatible con: Linux / macOS
# ============================================================

# --- Colores para la terminal ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}============================================${NC}"
    echo -e "${CYAN}${BOLD}  ChacalitosTCG - Instalador de Dependencias${NC}"
    echo -e "${CYAN}${BOLD}============================================${NC}"
    echo ""
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_ok() {
    echo -e "${GREEN}  ✔ $1${NC}"
}

print_error() {
    echo -e "${RED}  ✘ ERROR: $1${NC}"
}

print_header

# ---- Verificar Python ----
print_step "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 no está instalado. Por favor instálalo desde https://python.org"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
print_ok "Python encontrado: $PYTHON_VERSION"

# ---- Verificar pip ----
print_step "Verificando pip..."
if ! python3 -m pip --version &> /dev/null; then
    print_error "pip no está disponible. Intenta: sudo apt install python3-pip"
    exit 1
fi
print_ok "pip disponible."

# ---- Actualizar pip ----
print_step "Actualizando pip..."
python3 -m pip install --upgrade pip --quiet
print_ok "pip actualizado."

# ---- Instalar dependencias del sistema (Linux) ----
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_step "Detectado Linux. Instalando dependencias del sistema para Kivy y Buildozer (Android)..."
    echo -e "${YELLOW}  Se requieren permisos de superusuario (sudo).${NC}"

    if command -v apt-get &> /dev/null; then
        sudo apt-get update -y --quiet
        sudo apt-get install -y \
            python3-dev libsdl2-dev libsdl2-image-dev \
            libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev \
            libswscale-dev libavformat-dev libavcodec-dev \
            zlib1g-dev libgl1-mesa-dev libgles2-mesa-dev \
            git zip unzip openjdk-17-jdk autoconf libtool \
            pkg-config cmake libffi-dev libssl-dev lld \
            2>/dev/null || echo -e "${YELLOW}  ⚠ Algunos paquetes pueden no haberse instalado (quizás ya están presentes).${NC}"
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y \
            SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel \
            portmidi-devel ffmpeg-devel mesa-libGL-devel \
            git zip unzip java-17-openjdk-devel autoconf libtool \
            pkgconfig cmake libffi-devel openssl-devel \
            2>/dev/null || echo -e "${YELLOW}  ⚠ Algunos paquetes pueden no haberse instalado.${NC}"
    else
        echo -e "${YELLOW}  ⚠ Gestor de paquetes no reconocido. Instala manualmente las dependencias de Buildozer y SDL2.${NC}"
    fi
    print_ok "Dependencias del sistema verificadas."
fi

# ---- Instalar dependencias Python ----
echo ""
print_step "Instalando dependencias Python del proyecto..."
echo ""

DEPS=(
    "kivy[base]"
    "psutil"
    "requests"
    "PyJWT"
    "fastapi"
    "uvicorn[standard]"
    "pydantic"
    "passlib[bcrypt]"
    "cython"
    "buildozer"
)

LABELS=(
    "Kivy              (motor de UI principal)"
    "psutil            (monitoreo del sistema)"
    "requests          (peticiones HTTP / cloud sync)"
    "PyJWT             (tokens de autenticación)"
    "FastAPI           (servidor REST)"
    "uvicorn           (servidor ASGI para FastAPI)"
    "pydantic          (validación de datos)"
    "passlib[bcrypt]   (hashing de contraseñas)"
    "Cython            (compilador C para Android)"
    "Buildozer         (empaquetador APK para Android)"
)

FAILED=()

for i in "${!DEPS[@]}"; do
    dep="${DEPS[$i]}"
    label="${LABELS[$i]}"
    echo -ne "  Instalando ${BOLD}${label}${NC}..."
    if python3 -m pip install "$dep" --quiet 2>/dev/null; then
        echo -e " ${GREEN}✔${NC}"
    else
        echo -e " ${RED}✘ FALLÓ${NC}"
        FAILED+=("$dep")
    fi
done

# ---- Resumen ----
echo ""
echo -e "${CYAN}${BOLD}--- Resumen ---${NC}"
if [ ${#FAILED[@]} -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✔ Todas las dependencias instaladas correctamente.${NC}"
    echo ""
    echo -e "  Para ejecutar el proyecto localmente:  ${BOLD}python3 main.py${NC}"
    echo -e "  Para inicializar Buildozer (Android):  ${BOLD}buildozer init${NC}"
    echo -e "  Para compilar la APK Android:          ${BOLD}buildozer -v android debug${NC}"
else
    echo -e "${RED}${BOLD}✘ Las siguientes dependencias fallaron:${NC}"
    for f in "${FAILED[@]}"; do
        echo -e "  - $f"
    done
    echo ""
    echo -e "${YELLOW}  Instálalas manualmente con: pip install <nombre>${NC}"
fi
echo ""