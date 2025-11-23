"""AEDT CLI Main Entry Point

This module provides the main command-line interface for AEDT.
"""

import click
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aedt.core.config_manager import ConfigManager


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """AEDT - AI-Enhanced Delivery Toolkit

    智能 AI 开发编排引擎，支持并行开发和自动化工作流。
    """
    pass


@cli.command()
@click.option('--force', is_flag=True, help='覆盖已存在的配置')
@click.option('--global', 'is_global', is_flag=True, help='初始化全局配置 (~/.aedt/)')
def init(force: bool, is_global: bool):
    """初始化 AEDT 配置

    创建 .aedt/ 目录结构和默认配置文件。

    示例:
        aedt init              # 初始化项目配置
        aedt init --global     # 初始化全局配置
        aedt init --force      # 强制覆盖已存在的配置
    """
    try:
        config_mgr = ConfigManager()
        config_mgr.initialize(force=force, is_global=is_global)

        location = "全局" if is_global else "项目"
        click.echo(click.style(f'✓ AEDT {location}配置初始化成功', fg='green'))

        # Show created directory structure
        base_dir = Path.home() / ".aedt" if is_global else Path.cwd() / ".aedt"
        click.echo(f"\n创建的目录结构:")
        click.echo(f"  {base_dir}/")
        click.echo(f"  ├── config.yaml")
        click.echo(f"  ├── logs/")
        click.echo(f"  ├── projects/")
        click.echo(f"  └── worktrees/")

    except RuntimeError as e:
        click.echo(click.style(f'✗ 初始化失败: {e}', fg='red'), err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f'✗ 初始化失败: {e}', fg='red'), err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
