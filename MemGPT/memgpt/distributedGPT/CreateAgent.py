from memgpt.metadata import MetadataStore
from memgpt.config import MemGPTConfig
import questionary
from enum import Enum
from typing import Annotated, Optional
import typer
import requests
from memgpt.credentials import MemGPTCredentials
import os
from memgpt.data_types import EmbeddingConfig, LLMConfig, User
import json
import uuid
import sys
from memgpt.streaming_interface import StreamingRefreshCLIInterface as interface  # for printing to terminal
import memgpt.utils as utils
from memgpt.agent import Agent, save_agent




class QuickstartChoice(Enum):
    openai = "openai"
    # azure = "azure"
    memgpt_hosted = "memgpt"


def str_to_quickstart_choice(choice_str: str) -> QuickstartChoice:
    try:
        return QuickstartChoice[choice_str]
    except KeyError:
        valid_options = [choice.name for choice in QuickstartChoice]
        raise ValueError(f"{choice_str} is not a valid QuickstartChoice. Valid options are: {valid_options}")


def set_config_with_dict(new_config: dict) -> (MemGPTConfig, bool): # type: ignore
    """_summary_

    Args:
        new_config (dict): Dict of new config values

    Returns:
        new_config MemGPTConfig, modified (bool): Returns the new config and a boolean indicating if the config was modified
    """
    from memgpt.utils import printd

    old_config = MemGPTConfig.load()
    modified = False
    for k, v in vars(old_config).items():
        if k in new_config:
            if v != new_config[k]:
                printd(f"Replacing config {k}: {v} -> {new_config[k]}")
                modified = True
                # old_config[k] = new_config[k]
                setattr(old_config, k, new_config[k])  # Set the new value using dot notation
            else:
                printd(f"Skipping new config {k}: {v} == {new_config[k]}")

    # update embedding config
    if old_config.default_embedding_config:
        for k, v in vars(old_config.default_embedding_config).items():
            if k in new_config:
                if v != new_config[k]:
                    printd(f"Replacing config {k}: {v} -> {new_config[k]}")
                    modified = True
                    # old_config[k] = new_config[k]
                    setattr(old_config.default_embedding_config, k, new_config[k])
                else:
                    printd(f"Skipping new config {k}: {v} == {new_config[k]}")
    else:
        modified = True
        fields = ["embedding_model", "embedding_dim", "embedding_chunk_size", "embedding_endpoint", "embedding_endpoint_type"]
        args = {}
        for field in fields:
            if field in new_config:
                args[field] = new_config[field]
                printd(f"Setting new config {field}: {new_config[field]}")
        old_config.default_embedding_config = EmbeddingConfig(**args)

    # update llm config
    if old_config.default_llm_config:
        for k, v in vars(old_config.default_llm_config).items():
            if k in new_config:
                if v != new_config[k]:
                    printd(f"Replacing config {k}: {v} -> {new_config[k]}")
                    modified = True
                    # old_config[k] = new_config[k]
                    setattr(old_config.default_llm_config, k, new_config[k])
                else:
                    printd(f"Skipping new config {k}: {v} == {new_config[k]}")
    else:
        modified = True
        fields = ["model", "model_endpoint", "model_endpoint_type", "model_wrapper", "context_window"]
        args = {}
        for field in fields:
            if field in new_config:
                args[field] = new_config[field]
                printd(f"Setting new config {field}: {new_config[field]}")
        old_config.default_llm_config = LLMConfig(**args)
    return (old_config, modified)


def quickstart(
    backend: Annotated[QuickstartChoice, typer.Option(help="Quickstart setup backend")] = "memgpt",
    latest: Annotated[bool, typer.Option(help="Use --latest to pull the latest config from online")] = False,
    terminal: bool = True,
):
    """Set the base config file with a single command

    This function and `configure` should be the ONLY places where MemGPTConfig.save() is called.
    """
    # make sure everything is set up properly
    # Michael: MemGPTConfig.create_config_dir() creates a ~/.memgpt folder that presumably contains
    # all metadata for MemGPT to work correctly
    MemGPTConfig.create_config_dir()
    credentials = MemGPTCredentials.load()

    config_was_modified = False
    # adding this assertion instead of an if-conditional to prevent unnecessary nesting
    assert backend == QuickstartChoice.openai, "bruh we don't support any other backends rn"

    # Make sure we have an API key
    api_key = os.getenv("OPENAI_API_KEY")
    credentials.openai_key = api_key
    credentials.save()

    # TODO: load the file manually

    # Load the file from the relative path
    script_dir = os.path.dirname(__file__)  # Get the directory where the script is located
    backup_config_path = os.path.join(script_dir, "..", "configs", "openai.json")
    
    # the below lines basically update the metadata / config details in ~/.memgpt/config
    try:
        with open(backup_config_path, "r", encoding="utf-8") as file:
            backup_config = json.load(file)
        print("Loaded config file successfully.")
        new_config, config_was_modified = set_config_with_dict(backup_config)
    except FileNotFoundError:
        typer.secho(f"Config file not found at {backup_config_path}", fg=typer.colors.RED)
        return

    if config_was_modified:
        print(f"Saving new config file.")
        new_config.save()
        typer.secho(f"📖 MemGPT configuration file updated!", fg=typer.colors.GREEN)
        typer.secho(
            "\n".join(
                [
                    f"🧠 model\t-> {new_config.default_llm_config.model}",
                    f"🖥️  endpoint\t-> {new_config.default_llm_config.model_endpoint}",
                ]
            ),
            fg=typer.colors.GREEN,
        )
    else:
        typer.secho(f"📖 MemGPT configuration file unchanged.", fg=typer.colors.WHITE)
        typer.secho(
            "\n".join(
                [
                    f"🧠 model\t-> {new_config.default_llm_config.model}",
                    f"🖥️  endpoint\t-> {new_config.default_llm_config.model_endpoint}",
                ]
            ),
            fg=typer.colors.WHITE,
        )

    # 'terminal' = quickstart was run alone, in which case we should guide the user on the next command
    if terminal:
        if config_was_modified:
            typer.secho('⚡ Run "memgpt run" to create an agent with the new config.', fg=typer.colors.YELLOW)
        else:
            typer.secho('⚡ Run "memgpt run" to create an agent.', fg=typer.colors.YELLOW)

def create_default_user_or_exit(config: MemGPTConfig, ms: MetadataStore):
    user_id = uuid.UUID(config.anon_clientid)
    user = ms.get_user(user_id=user_id)
    if user is None:
        ms.create_user(User(id=user_id))
        user = ms.get_user(user_id=user_id)
        if user is None:
            typer.secho(f"Failed to create default user in database.", fg=typer.colors.RED)
            sys.exit(1)
        else:
            return user
    else:
        return user

def main(
  preset: Annotated[Optional[str], typer.Option(help="Specify preset")] = None,
  model: Annotated[Optional[str], typer.Option(help="Specify the LLM model")] = None,
  ):
  # set config
  
  config_choices = {
    "openai": "Use OpenAI (requires an OpenAI API key)",
  }
  print()
  config_selection = questionary.select(
    "How would you like to set up MemGPT?",
    choices=list(config_choices.values()),
    default=config_choices["openai"],
  ).ask()

  if config_selection == config_choices["openai"]:
      print()
      quickstart(backend=QuickstartChoice.openai, terminal=False, latest=False)
  else:
      raise ValueError(config_selection)

  config = MemGPTConfig.load()

  ms = MetadataStore(config)
  
  
  try:
      user = create_default_user_or_exit(config, ms)
      human = config.human
      persona = config.persona
      
      breakpoint()
      preset_obj = ms.get_preset(name=config.preset, user_id=user.id)
      human_obj = ms.get_human(human, user.id)
      persona_obj = ms.get_persona(persona, user.id)
      
      agent_name = utils.create_random_username()
      llm_config = config.default_llm_config
      embedding_config = config.default_embedding_config  # TODO allow overriding embedding params via CLI run
      
      if preset_obj is None:
          # create preset records in metadata store
          from memgpt.presets.presets import add_default_presets

          add_default_presets(user.id, ms)
          # try again
          preset_obj = ms.get_preset(name=preset if preset else config.preset, user_id=user.id)
          if preset_obj is None:
              typer.secho("Couldn't find presets in database, please run `memgpt configure`", fg=typer.colors.RED)
              sys.exit(1)
      if human_obj is None:
          typer.secho("Couldn't find human {human} in database, please run `memgpt add human`", fg=typer.colors.RED)
      if persona_obj is None:
          typer.secho("Couldn't find persona {persona} in database, please run `memgpt add persona`", fg=typer.colors.RED)

      # Overwrite fields in the preset if they were specified
      preset_obj.human = ms.get_human(human, user.id).text
      preset_obj.persona = ms.get_persona(persona, user.id).text

      typer.secho(f"->  🤖 Using persona profile: '{preset_obj.persona_name}'", fg=typer.colors.WHITE)
      typer.secho(f"->  🧑 Using human profile: '{preset_obj.human_name}'", fg=typer.colors.WHITE)

      memgpt_agent = Agent(
          interface=interface(),
          name=agent_name,
          created_by=user.id,
          preset=preset_obj,
          llm_config=llm_config,
          embedding_config=embedding_config,
          # gpt-3.5-turbo tends to omit inner monologue, relax this requirement for now
          first_message_verify_mono=True if (model is not None and "gpt-4" in model) else False,
      )
      save_agent(agent=memgpt_agent, ms=ms)

  except ValueError as e:
      typer.secho(f"Failed to create agent from provided information:\n{e}", fg=typer.colors.RED)
      sys.exit(1)
  typer.secho(f"🎉 Created new agent '{memgpt_agent.agent_state.name}' (id={memgpt_agent.agent_state.id})", fg=typer.colors.GREEN)

main()
