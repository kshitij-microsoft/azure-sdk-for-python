# CoPilot instructions for azure-ai-projects development

## Prerequisite

* Clone the `azure-sdk-for-python` repo to you local machine, if you don't already have it:
  ```
  git clone https://github.com/Azure/azure-sdk-for-python.git
  ```
* Change to the directory `sdk\ai\azure-ai-projects`. 
* Switch to the current feature branch: `git switch feature/azure-ai-projects/2.2.0`.
* Make sure you don't have any filed edited or added in this branch (clean `git status` state).

## Emit from TypeSpec and create a PR

### Using GitHub CoPilot in VSCode

* Open a VSCode in the current folder.
* Open the CoPilot chat window ("Toggle Chat").
* Optional: List all instructions by typing `/instructions`. Make sure you see `azure-ai-projects.emit-from-typespec` listed. 
* Type `@azure-ai-projects` and then tab to complete the selection of `@file:azure-ai-projects.emit-from-typespec.instructions.md`
* Answer some questions and approve execution to go through the workflow

### Using CoPilot CLI or Agency Copilot CLI

* Install [GitHub CoPilot CLI](https://docs.github.com/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli) or [Agency CoPilot CLI](https://aka.ms/agency) (VPN required) if you don't already have it.
* Run CoPilot CLI by typing `copilot`
* Optional: List all instructions by typing `/instructions`. You should see `azure-ai-projects.emit-from-typespec.instructions.md` listed. Press `ESC` to get back to the command prompt.
* Type `@azure-ai-projects` and then press enter to accept the instructions `@.github\instructions\azure-ai-projects.emit-from-typespec.instructions.md`
* Answer some questions and approve execution to go through the workflow






