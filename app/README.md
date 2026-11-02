This folder will hold the desktop and mobile app for the homebrew assistant.
Currently, I'm using Ubuntu 26.04 as operating system and all the tools are installed to that.

## Toolchain

| Tool                       | Version  | Install command                                                                                                                                                                                  | Version command          |
|----------------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------|
| .NET SDK                   | 10.0.114 | `sudo apt-get install -y dotnet-sdk-10.0`                                                                                                                                                        | `dotnet --list-sdks`     |
| nvm                        | 0.40.3   | `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh \| bash`                                                                                                              | `nvm --version`          |
| Node.js                    | 26.13.0  | `nvm install 26.13.0` <br> `nvm alias default 26`                                                                                                                                                | `node -v`                |
| npm                        | 11.20.0  | comes with Node.js                                                                                                                                                                               | `npm -v`                 |
| typescript                 | 7.0.2    | `npm install -g typescript`                                                                                                                                                                      | `npm ls -g --depth=0`    |
| typescript-language-server | 6.0.3    | `npm install -g typescript-language-server`                                                                                                                                                      | `npm ls -g --depth=0`    |
| csharp-ls                  | 0.28.0   | `dotnet tool install --global csharp-ls`                                                                                                                                                         | `csharp-ls --version`    |
| IDE (Rider)                | 2026.2.4 | install tar from [website](https://www.jetbrains.com/rider/download/?section=linux) <br> `sudo tar -xzf jetbrains-rider-*.tar.gz -C /opt/` <br> start: `"/opt/JetBrains Rider-2026.2.4/bin/rider.sh"` | Help > About             |
