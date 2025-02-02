import pathlib

import typer

from _nebari.config import read_configuration
from _nebari.deploy import deploy_configuration
from _nebari.render import render_template
from nebari.hookspecs import hookimpl

TERRAFORM_STATE_STAGE_NAME = "01-terraform-state"


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command()
    def deploy(
        ctx: typer.Context,
        config_filename: pathlib.Path = typer.Option(
            ...,
            "--config",
            "-c",
            help="nebari configuration yaml file path",
        ),
        output_directory: pathlib.Path = typer.Option(
            "./",
            "-o",
            "--output",
            help="output directory",
        ),
        dns_provider: str = typer.Option(
            False,
            "--dns-provider",
            help="dns provider to use for registering domain name mapping ⚠️ moved to `dns.provider` in nebari-config.yaml",
        ),
        dns_auto_provision: bool = typer.Option(
            False,
            "--dns-auto-provision",
            help="Attempt to automatically provision DNS, currently only available for `cloudflare` ⚠️ moved to `dns.auto_provision` in nebari-config.yaml",
        ),
        disable_prompt: bool = typer.Option(
            False,
            "--disable-prompt",
            help="Disable human intervention",
        ),
        disable_render: bool = typer.Option(
            False,
            "--disable-render",
            help="Disable auto-rendering in deploy stage",
        ),
        disable_checks: bool = typer.Option(
            False,
            "--disable-checks",
            help="Disable the checks performed after each stage",
        ),
        skip_remote_state_provision: bool = typer.Option(
            False,
            "--skip-remote-state-provision",
            help="Skip terraform state deployment which is often required in CI once the terraform remote state bootstrapping phase is complete",
        ),
    ):
        """
        Deploy the Nebari cluster from your [purple]nebari-config.yaml[/purple] file.
        """
        from nebari.plugins import nebari_plugin_manager

        stages = nebari_plugin_manager.ordered_stages
        config_schema = nebari_plugin_manager.config_schema

        config = read_configuration(config_filename, config_schema=config_schema)

        if not disable_render:
            render_template(output_directory, config, stages)

        if skip_remote_state_provision:
            for stage in stages:
                if stage.name == TERRAFORM_STATE_STAGE_NAME:
                    stages.remove(stage)
            print("Skipping remote state provision")

        if dns_provider and dns_auto_provision:
            # TODO: Add deprecation warning and update docs on how to configure DNS via nebari-config.yaml
            print(
                "Please add a `dns.provider` and `dns.auto_privision` to your nebari-config.yaml file to enable DNS auto-provisioning."
            )
            exit(1)

        deploy_configuration(
            config,
            stages,
            disable_prompt=disable_prompt,
            disable_checks=disable_checks,
        )
