{ pkgs, lib, ... }:

{
  # --- Python 3.12 with project + dev dependencies ---
  languages.python = {
    enable = true;
    package = pkgs.python312;

    # Use a venv so pip-installed packages (faster-whisper, openwakeword)
    # coexist with Nix-provided ones.
    venv = {
      enable = true;
      requirements = ''
        # Runtime
        sounddevice
        numpy
        requests
        faster-whisper
        onnxruntime
        edge-tts
        openwakeword

        # Dev
        pytest
        ruff
        mypy
        types-requests
      '';
    };
  };

  # --- Native libraries needed on NixOS ---
  # numpy/onnxruntime need libstdc++; sounddevice needs portaudio;
  # numpy also links libz.
  env.LD_LIBRARY_PATH = lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.portaudio
    pkgs.zlib
  ];

  # PipeWire access for audio playback / recording
  env.XDG_RUNTIME_DIR = builtins.getEnv "XDG_RUNTIME_DIR";

  # --- Extra packages available in the shell ---
  # NOTE: openai-whisper is NOT included here because its nixpkgs derivation
  # brings Python 3.13 deps that conflict with our Python 3.12 venv.
  # On NixOS, whisper is available system-wide at /run/current-system/sw/bin/whisper.
  # For non-NixOS, install it separately or set WHISPER_BIN.
  packages = [
    pkgs.mpv    # audio playback
    pkgs.ffmpeg # audio conversion
  ];

  # --- Convenience scripts ---
  scripts.test.exec = "pytest $@";
  scripts.test.description = "Run pytest";

  scripts.lint.exec = "ruff check $@";
  scripts.lint.description = "Lint with ruff";

  scripts.format.exec = "ruff format $@";
  scripts.format.description = "Format with ruff";

  scripts.typecheck.exec = "mypy hey_cleber/ $@";
  scripts.typecheck.description = "Type-check with mypy";

  scripts.check.exec = ''
    set -e
    echo "==> lint"
    ruff check
    echo "==> typecheck"
    mypy hey_cleber/
    echo "==> test"
    pytest
    echo "✅ All checks passed"
  '';
  scripts.check.description = "Run lint + typecheck + tests";

  scripts.run.exec = "python -m hey_cleber $@";
  scripts.run.description = "Run hey-cleber locally";

  # --- Pre-commit hooks (lightweight, no extra CI infra) ---
  git-hooks.hooks = {
    ruff.enable = true;
    ruff-format.enable = true;
  };
}
