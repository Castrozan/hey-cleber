{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  pythonWithPackages = python.withPackages (ps: with ps; [
    numpy
    requests
    sounddevice
    # openwakeword and edge-tts are installed via pip in the venv
  ]);
in
pkgs.mkShell {
  name = "hey-cleber";

  buildInputs = with pkgs; [
    pythonWithPackages
    portaudio       # needed by sounddevice
    ffmpeg
    mpv
    espeak-ng       # fallback TTS
  ];

  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.portaudio}/lib:${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
    export XDG_RUNTIME_DIR="/run/user/1000"

    # Create/activate venv for pip-only packages
    VENV_DIR="$HOME/.local/share/hey-cleber-venv"
    if [ ! -d "$VENV_DIR" ]; then
      echo "Creating venv at $VENV_DIR ..."
      python3 -m venv --system-site-packages "$VENV_DIR"
      source "$VENV_DIR/bin/activate"
      pip install --upgrade pip
      pip install openwakeword edge-tts
    else
      source "$VENV_DIR/bin/activate"
    fi

    echo ""
    echo "=== Hey Cleber environment ready ==="
    echo "Run: python3 ~/clawd/scripts/hey-cleber.py"
    echo "Or:  python3 ~/clawd/scripts/hey-cleber.py --list-devices"
    echo ""
  '';
}
