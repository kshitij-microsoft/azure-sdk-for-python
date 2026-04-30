# CoPilot CLI instructions for azure-ai-projects development

* Install [GitHub CoPilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli), if you don't already have it.
* Clone the `azure-sdk-for-python` repo to you local machine, if you don't already have it:
  ```
  git clone https://github.com/Azure/azure-sdk-for-python.git
  ```
* Change to the directory `sdk\ai\azure-ai-projects` 
* Switch to the current feature branch: `git switch feature/azure-ai-projects/2.2.0`
* Run CoPilot CLI by typing `copilot`
* List all instructions by typing `/instructions`. You should see `azure-ai-projects.emit-from-typespec.instructions.md` listed. Press `ESC` to get back to the command prompt.

## Emit from TypeSpec and create a PR

* Type `@azure-ai-projects` and then press enter to accept the instructions `@.github\instructions\azure-ai-projects.emit-from-typespec.instructions.md`
* Answer some questions and approve execution to go through the workflow






