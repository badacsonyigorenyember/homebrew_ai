This folder will hold the desktop and mobile app for the homebrew assistant.
Currently, I'm using Ubuntu 26.04 as operating system and all the tools are installed to that.

## Toolchain

| Tool                       | Version   | Install command                                                                                                                            | Version command           |
|----------------------------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| .NET SDK                   | 10.0.1145 | `sudo apt-get install -y dotnet-sdk-10.0`                                                                                                  | `dotnet --list-sdks`      |
| npm                        | 10.9.7    | `npm install -g npm@10.9.7`                                                                                                                | `npm -v`                  |
| nvm                        | 0.40.3    | `curl -o- https://githubusercontent.com \| bash `                                                                                          | `nvm alias default` is 26 |
| Node.js                    | 26.13.0   | `nvm install 26.13.0`                                                                                                                      | `node -v`                 |
| typescript                 | 7.0.2     | `npm install -g typescript`                                                                                                                | `npm ls -g --depth=0`     |
| typescript-language-server | 6.0.2     | `npm install -g typescript-language-server`                                                                                                | `npm ls -g --depth=0`     |
| csharp-ls                  | 0.28      | `dotnet tool install --global csharp-ls`                                                                                                   | `csharp-ls -v`            |
| IDE (Rider)                | 2026.2.4  | install tar from [website](https://www.jetbrains.com/rider/download/?section=linux) <br> `sudo tar -xzf jetbrains-rider-*.tar.gz -C /opt/` | -                         |