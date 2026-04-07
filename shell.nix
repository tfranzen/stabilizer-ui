{ pkgs ? import <nixpkgs> {} }:

let
  fhs = pkgs.buildFHSEnv {
    name = "stabilizer-ui-env";

    targetPkgs = pkgs: [
      pkgs.poetry
      pkgs.python312

      # GPU / GL
      pkgs.mesa
      pkgs.libGL
      pkgs.libGLU

      # X11
      pkgs.xorg.libX11
      pkgs.xorg.libXext
      pkgs.xorg.libXrender
      pkgs.xorg.libXfixes
      pkgs.xorg.libXi
      pkgs.xorg.libXcursor
      pkgs.xorg.libXrandr
      pkgs.xorg.libXinerama
      pkgs.xorg.xcbutilcursor

      # Wayland
      pkgs.wayland
      pkgs.libxkbcommon

      # Font/text
      pkgs.fontconfig
      pkgs.freetype

      # GLib
      pkgs.glib
      pkgs.pango
      pkgs.gdk-pixbuf

      pkgs.dbus
      pkgs.zstd
    ];

    runScript = "${pkgs.bash}/bin/bash";
  };
in

# ✅ This makes `nix-shell` actually launch the FHS environment
fhs.env
