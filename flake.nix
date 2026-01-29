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

      # Wrapper that uses a managed venv and runs the package
      hey-cleber = pkgs.writeShellScriptBin "hey-cleber" ''
        VENV_DIR="''${HEY_CLEBER_VENV:-$HOME/.local/share/hey-cleber-venv}"
        PACKAGE_DIR="${self}/hey_cleber"

        export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.portaudio}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        export PATH="${pkgs.ffmpeg}/bin:${pkgs.mpv}/bin:${pkgs.openai-whisper}/bin:$PATH"
        export XDG_RUNTIME_DIR="''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
        export PYTHONPATH="${self}''${PYTHONPATH:+:$PYTHONPATH}"

        if [ ! -d "$VENV_DIR" ]; then
          echo "Setting up Hey Cleber venv at $VENV_DIR ..."
          ${python}/bin/python3 -m venv "$VENV_DIR"
          source "$VENV_DIR/bin/activate"
          pip install --upgrade pip setuptools wheel >/dev/null 2>&1
          pip install faster-whisper openwakeword sounddevice numpy requests edge-tts onnxruntime 2>&1
        else
          source "$VENV_DIR/bin/activate"
        fi

        exec python3 -m hey_cleber "$@"
      '';
    in
    {
      packages.${system} = {
        default = hey-cleber;
        inherit hey-cleber;
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          python
          pkgs.python312Packages.numpy
          pkgs.python312Packages.requests
          pkgs.python312Packages.pytest
          pkgs.ruff
        ];
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
              description = "Extra arguments to pass to hey-cleber";
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
