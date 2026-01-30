{
  description = "Hey Clever — Always-on voice assistant powered by Clawdbot";

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
      hey-clever = pkgs.writeShellScriptBin "hey-clever" ''
        VENV_DIR="''${HEY_CLEVER_VENV:-$HOME/.local/share/hey-clever-venv}"
        PACKAGE_DIR="${self}/hey_clever"

        export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.portaudio}/lib:${pkgs.zlib}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        export PATH="${pkgs.ffmpeg}/bin:${pkgs.mpv}/bin:${pkgs.openai-whisper}/bin:$PATH"
        export XDG_RUNTIME_DIR="''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
        export PYTHONPATH="${self}''${PYTHONPATH:+:$PYTHONPATH}"

        if [ ! -d "$VENV_DIR" ]; then
          echo "Setting up Hey Clever venv at $VENV_DIR ..."
          ${python}/bin/python3 -m venv "$VENV_DIR"
          source "$VENV_DIR/bin/activate"
          pip install --upgrade pip setuptools wheel >/dev/null 2>&1
          pip install faster-whisper openwakeword sounddevice numpy requests edge-tts onnxruntime 2>&1
        else
          source "$VENV_DIR/bin/activate"
        fi

        exec python3 -m hey_clever "$@"
      '';
    in
    {
      packages.${system} = {
        default = hey-clever;
        inherit hey-clever;
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
      homeManagerModules.default = self.homeManagerModules.hey-clever;
      homeManagerModules.hey-clever =
        {
          config,
          lib,
          pkgs,
          ...
        }:
        let
          cfg = config.services.hey-clever;
        in
        {
          options.services.hey-clever = {
            enable = lib.mkEnableOption "Hey Clever voice assistant";

            keywords = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = [
                "clever"
                "klever"
                "cleber"
                "kleber"
                "cleaver"
                "clevert"
                "kleiber"
                "klebber"
                "cleyber"
              ];
              description = "Activation keywords for wake word detection";
            };

            gatewayUrl = lib.mkOption {
              type = lib.types.str;
              default = "http://localhost:18789";
              description = "Clawdbot gateway URL";
            };

            gatewayToken = lib.mkOption {
              type = lib.types.str;
              default = "";
              description = "Gateway authentication token. Set via this option or CLAWDBOT_GATEWAY_TOKEN env var.";
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
              description = "Extra arguments to pass to hey-clever";
            };

            package = lib.mkOption {
              type = lib.types.package;
              default = hey-clever;
              description = "The hey-clever package to use";
            };
          };

          config = lib.mkIf cfg.enable {
            home.packages = [ cfg.package ];

            systemd.user.services.hey-clever = {
              Unit = {
                Description = "Hey Clever Voice Assistant";
                After = [
                  "pipewire.service"
                  "pipewire-pulse.service"
                ];
                Wants = [ "pipewire.service" ];
              };

              Service = {
                Type = "simple";
                ExecStart =
                  let
                    keywordsArg = "--keywords ${lib.concatStringsSep "," cfg.keywords}";
                    extraArgsStr = lib.concatStringsSep " " cfg.extraArgs;
                  in
                  "${cfg.package}/bin/hey-clever ${keywordsArg} ${extraArgsStr}";
                Restart = "on-failure";
                RestartSec = "5s";
                Environment = [
                  "CLAWDBOT_GATEWAY_URL=${cfg.gatewayUrl}"
                  "WHISPER_BIN=${cfg.whisperBin}"
                  "MPV_BIN=${cfg.mpvBin}"
                ]
                ++ lib.optional (cfg.gatewayToken != "") "CLAWDBOT_GATEWAY_TOKEN=${cfg.gatewayToken}";
              };

              Install = {
                WantedBy = [ "default.target" ];
              };
            };
          };
        };
    };
}
