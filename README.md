# WSL Orchestrator

A lightweight, multi-language GUI tool for managing Windows Subsystem for Linux (WSL2) instances. Developed under the banner of `Project Ishikori`.

![WSL Orchestrator Screenshot](https://storage.googleapis.com/maker-suit-tool-images/uploaded-files/image_9714a2.png)

## Overview

`WSL Orchestrator` aims to simplify the daily workflow of WSL users by providing an intuitive interface for common management tasks. This tool was built with a philosophy of "Simple Experience, Complex Internals," providing robust functionality in a user-friendly package.

## Features

-   **Instance Management**: View the status of all your WSL instances at a glance.
-   **Core Actions**: Start, Terminate, and Shutdown all instances with a single click.
-   **Safe Rename**: Rename distributions safely. The app includes checks to prevent renaming to a duplicate name.
-   **Multi-Language Support**: UI available in English, Japanese, Spanish, French, Arabic, and Hindi. The language setting is saved for the next session.
-   **Dynamic UI**: The window automatically sizes to its content and has a minimum size set to prevent layout issues.
-   **Shortcut Helper**: Instantly generate the correct command to create a desktop shortcut for any of your instances.

## Getting Started

### Option 1: Using the EXE file (Recommended)

1.  Go to the [Releases](https://github.com/hkurocat/WSL_Orchestrator/releases) page.
2.  Download the latest `WSL_Orchestrator.zip` file.
3.  Unzip the package and run `WSL_Orchestrator.exe`.

### Option 2: Running from Source

1.  Ensure you have Python 3 installed.
2.  Clone this repository.
3.  The application requires no external libraries. Simply run the script from your terminal:
    ```bash
    python app.py
    ```

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the [issues page](https://github.com/hkurocat/WSL_Orchestrator/issues). Please note our code of conduct and stick to the project's design philosophy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.