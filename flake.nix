{
  description = "Hey Cleber — Always-on voice assistant powered by Clawdbot";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };

      python = pkgs.python312;

      pythonEnv = python.withPackages (
        ps: with ps; [
          numpy
          sounddevice
          requests
          onnxruntime
          edge-tts
        ]
      );

      # faster-whisper and openwakeword are not in nixpkgs, install via pip overlay
      hey-cleber-venv = pkgs.stdenv.mkDerivation {
        pname = "hey-cleber-venv";
        version = "1.0.0";
        src = ./.;

        nativeBuildInputs = [
          python
          pkgs.python312Packages.pip
          pkgs.python312Packages.setuptools
          pkgs.python312Packages.wheel
        ];

        buildInputs = [
          pkgs.portaudio
          pkgs.stdenv.cc.cc.lib
        ];

        buildPhase = ''
          export HOME=$TMPDIR
          ${python}/bin/python3 -m venv $TMPDIR/venv --system-site-packages
          source $TMPDIR/venv/bin/activate
          pip install --no-cache-dir \
            faster-whisper \
            openwakeword \
            sounddevice \
            numpy \
            requests \
            edge-tts \
            onnxruntime
        '';

        installPhase = ''
          mkdir -p $out/lib/hey-cleber
          cp -r $TMPDIR/venv/* $out/lib/hey-cleber/

          # Copy the script
          mkdir -p $out/share/hey-cleber
          cp hey-cleber.py $out/share/hey-cleber/

          # Create wrapper script
          mkdir -p $out/bin
          cat > $out/bin/hey-cleber <<'WRAPPER'
          #!/usr/bin/env bash
          SCRIPT_DIR="@out@/share/hey-cleber"
          VENV_DIR="@out@/lib/hey-cleber"
          export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.portaudio}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
          export PATH="${pkgs.ffmpeg}/bin:${pkgs.mpv}/bin:${pkgs.openai-whisper}/bin:$PATH"
          source "$VENV_DIR/bin/activate"
          exec python3 "$SCRIPT_DIR/hey-cleber.py" "$@"
          WRAPPER
          substituteInPlace $out/bin/hey-cleber --replace "@out@" "$out"
          chmod +x $out/bin/hey-cleber
        '';
      };

      # Simpler approach: just a wrapper that uses a managed venv
      hey-cleber = pkgs.writeShellScriptBin "hey-cleber" ''
        VENV_DIR="''${HEY_CLEBER_VENV:-$HOME/.local/share/hey-cleber-venv}"
        SCRIPT="${self}/hey-cleber.py"

        export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.portaudio}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        export PATH="${pkgs.ffmpeg}/bin:${pkgs.mpv}/bin:${pkgs.openai-whisper}/bin:$PATH"
        export XDG_RUNTIME_DIR="''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

        if [ ! -d "$VENV_DIR" ]; then
          echo "Setting up Hey Cleber venv at $VENV_DIR ..."
          ${python}/bin/python3 -m venv "$VENV_DIR"
          source "$VENV_DIR/bin/activate"
          pip install --upgrade pip setuptools wheel >/dev/null 2>&1
          pip install faster-whisper openwakeword sounddevice numpy requests edge-tts onnxruntime 2>&1
        else
          source "$VENV_DIR/bin/activate"
        fi

        exec python3 "$SCRIPT" "$@"
      '';
    in
    {
      packages.${system} = {
        default = hey-cleber;
        inherit hey-cleber;
      };

      # Home Manager module
      homeManagerModules.default = self.homeManagerModules.hey-cleber;
      homeManagerModules.hey-cleber =
        { config, lib, pkgs, ... }:
        let
          cfg = config.services.hey-cleber;
        in
        {
          options.services.hey-cleber = {
            enable = lib.mkEnableOption "Hey Cleber voice assistant";

            keywords = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = [
                "cleber"
                "kleber"
                "clever"
                "cleaver"
                "clebert"
                "kleiber"
                "klebber"
                "cleyber"
                "klever"
              ];
              description = "Activation keywords for wake word detection";
            };

            gatewayUrl = lib.mkOption {
              type = lib.types.str;
              default = "http://localhost:18789";
              description = "Clawdbot gateway URL";
            };

            gatewayTokenFile = lib.mkOption {
              type = lib.types.nullOr lib.types.path;
              default = null;
              description = "Path to file containing the gateway token. If null, uses CLAWDBOT_GATEWAY_TOKEN env var.";
            };

            whisperBin = lib.mkOption {
              type = lib.types.str;
              default = "${pkgs.openai-whisper}/bin/whisper";
              description = "Path to Whisper CLI binary";
            };

            mpvBin = lib.mkOption {
              type = lib.types.str;
              default = "${pkgs.mpv}/bin/mpv";
              description = "Path to mpv binary";
            };

            extraArgs = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = [ ];
              description = "Extra arguments to pass to hey-cleber.py";
            };

            package = lib.mkOption {
              type = lib.types.package;
              default = hey-cleber;
              description = "The hey-cleber package to use";
            };
          };

          config = lib.mkIf cfg.enable {
            home.packages = [ cfg.package ];

            systemd.user.services.hey-cleber = {
              Unit = {
                Description = "Hey Cleber Voice Assistant";
                After = [ "pipewire.service" "pipewire-pulse.service" ];
                Wants = [ "pipewire.service" ];
              };

              Service = {
                Type = "simple";
                ExecStart =
                  let
                    keywordsArg = "--keywords ${lib.concatStringsSep "," cfg.keywords}";
                    extraArgsStr = lib.concatStringsSep " " cfg.extraArgs;
                  in
                  "${cfg.package}/bin/hey-cleber ${keywordsArg} ${extraArgsStr}";
                Restart = "on-failure";
                RestartSec = "5s";
                Environment = [
                  "CLAWDBOT_GATEWAY_URL=${cfg.gatewayUrl}"
                  "WHISPER_BIN=${cfg.whisperBin}"
                  "MPV_BIN=${cfg.mpvBin}"
                ];
              };

              Install = {
                WantedBy = [ "default.target" ];
              };
            };
          };
        };
    };
}
