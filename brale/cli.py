#!/usr/bin/env python3
"""Brale CLI - Command-line interface for the Brale API."""

import click
import json
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.status import Status
from rich.syntax import Syntax
from .config import config as brale_config
from .auth import auth as brale_auth, api_client

console = Console()

@click.group()
@click.option('--account', help='Account ID to use (overrides default)')
@click.option('--output', type=click.Choice(['table', 'json', 'yaml']), default='table', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def main(ctx, account, output, verbose):
    """Brale CLI - Interact with the Brale API from the command line."""
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)
    
    # Store global options in context
    ctx.obj['account'] = account
    ctx.obj['output'] = output
    ctx.obj['verbose'] = verbose
    
    if verbose:
        console.print(f"[dim]Brale CLI v{__import__('brale').__version__}[/dim]")

@main.group()
@click.pass_context
def auth(ctx):
    """Authentication commands."""
    pass

@main.group()
@click.pass_context
def accounts(ctx):
    """Account management commands."""
    pass

@main.group()
@click.pass_context
def addresses(ctx):
    """Address management commands."""
    pass

@main.group()
@click.pass_context
def transfers(ctx):
    """Transfer management commands."""
    pass

@main.group()
@click.pass_context
def automations(ctx):
    """Automation management commands."""
    pass

@main.group()
@click.pass_context
def config(ctx):
    """Configuration management commands."""
    pass

# Config commands
@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration."""
    output_format = ctx.obj['output']
    config_data = brale_config.to_dict()
    
    if output_format == 'json':
        console.print(json.dumps(config_data, indent=2))
    elif output_format == 'yaml':
        console.print(yaml.dump(config_data, default_flow_style=False))
    else:
        table = Table(title="Brale CLI Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config_data.items():
            table.add_row(key, str(value))
        
        console.print(table)

@config.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """Set a configuration value."""
    try:
        brale_config.set(key, value)
        console.print(f"[green]Set[/green] [cyan]{key}[/cyan] = [yellow]{value}[/yellow]")
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error setting configuration[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@config.command()
@click.argument('key')
def get(key):
    """Get a configuration value."""
    value = brale_config.get(key)
    if value is None:
        console.print(Panel.fit(
            f"[bold red]Configuration key not found[/bold red]\n'{key}' is not set",
            border_style="red"
        ))
        raise click.Abort()
    console.print(f"[cyan]{key}[/cyan] = [yellow]{value}[/yellow]")

# Auth commands
@auth.command()
@click.option('--client-id', help='Client ID (or set BRALE_CLIENT_ID)')
@click.option('--client-secret', help='Client secret (or set BRALE_SECRET)')
def login(client_id, client_secret):
    """Authenticate with Brale API."""
    with Status("[bold green]Authenticating...", console=console):
        try:
            success = brale_auth.authenticate(client_id, client_secret)
            if success:
                console.print(Panel.fit(
                    "[bold green]Authentication Successful[/bold green]",
                    border_style="green"
                ))
        
        except Exception as e:
            console.print(Panel.fit(
                f"[bold red]Authentication Failed[/bold red]\n{e}",
                border_style="red"
            ))
            raise click.Abort()
    
    # Test the authentication by fetching accounts
    with Status("[dim]Verifying access...", console=console):
        try:
            response = api_client.get('/accounts')
            if response.status_code == 200:
                accounts = response.json().get('accounts', [])
                console.print(f"[dim]Found {len(accounts)} account(s)[/dim]")
                
                # Auto-set default account if only one exists
                if len(accounts) == 1:
                    brale_config.set_default_account(accounts[0])
                    console.print(f"[dim]Set default account: [cyan]{accounts[0]}[/cyan][/dim]")
            else:
                console.print(f"[yellow]Warning: Couldn't fetch accounts (HTTP {response.status_code})[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Couldn't verify access: {e}[/yellow]")

@auth.command()
def status():
    """Check authentication status."""
    if brale_auth.is_authenticated():
        # Try to get basic info
        with Status("[dim]Checking access...", console=console):
            try:
                response = api_client.get('/accounts')
                if response.status_code == 200:
                    accounts = response.json().get('accounts', [])
                    console.print(Panel.fit(
                        f"[bold green]Authenticated[/bold green]\nAccess to {len(accounts)} account(s)",
                        border_style="green",
                        title="Authentication Status"
                    ))
                else:
                    console.print(Panel.fit(
                        f"[yellow]Token exists but API returned HTTP {response.status_code}[/yellow]",
                        border_style="yellow",
                        title="Authentication Status"
                    ))
            except Exception as e:
                console.print(Panel.fit(
                    f"[yellow]Token exists but couldn't verify: {e}[/yellow]",
                    border_style="yellow",
                    title="Authentication Status"
                ))
    else:
        console.print(Panel.fit(
            "[bold red]Not authenticated[/bold red]\nRun [cyan]brale auth login[/cyan] to authenticate",
            border_style="red",
            title="Authentication Status"
        ))

@auth.command()
def logout():
    """Clear stored authentication."""
    brale_auth.logout()
    console.print(Panel.fit(
        "[bold blue]Logged out successfully[/bold blue]",
        border_style="blue"
    ))

# Accounts commands
@accounts.command('list')
@click.pass_context
def list_accounts(ctx):
    """List all accounts."""
    try:
        response = api_client.get('/accounts')
        
        if response.status_code != 200:
            console.print(Panel.fit(
                f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                border_style="red",
                title="Error Fetching Accounts"
            ))
            raise click.Abort()
            
        data = response.json()
        accounts = data.get('accounts', [])
        
        output_format = ctx.obj['output']
        
        if output_format == 'json':
            syntax = Syntax(json.dumps(data, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif output_format == 'yaml':
            syntax = Syntax(yaml.dump(data, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            if not accounts:
                console.print(Panel.fit(
                    "[dim]No accounts found[/dim]",
                    border_style="yellow"
                ))
                return
                
            table = Table(title="Accounts")
            table.add_column("Account ID", style="cyan")
            table.add_column("Status", style="green")
            
            default_account = brale_config.get_default_account()
            
            for account_id in accounts:
                status = "default" if account_id == default_account else "active"
                table.add_row(account_id, status)
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(accounts)} account(s)[/dim]")
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@accounts.command()
@click.argument('account_id')
@click.pass_context
def show(ctx, account_id):
    """Show account details."""
    try:
        # For now, we'll just show the account ID since the API doesn't seem to have detailed account info
        # In a real implementation, you'd call GET /accounts/{account_id} if that endpoint exists
        
        output_format = ctx.obj['output']
        default_account = brale_config.get_default_account()
        
        account_info = {
            'id': account_id,
            'is_default': account_id == default_account
        }
        
        if output_format == 'json':
            console.print(json.dumps(account_info, indent=2))
        elif output_format == 'yaml':
            console.print(yaml.dump(account_info, default_flow_style=False))
        else:
            table = Table(title=f"Account Details: {account_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Account ID", account_id)
            table.add_row("Is Default", "✅ Yes" if account_info['is_default'] else "❌ No")
            
            console.print(table)
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

# Addresses commands
@addresses.command('list')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.pass_context
def list_addresses(ctx, account):
    """List all addresses for an account."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        response = api_client.get(f'/accounts/{account_id}/addresses')
        
        if response.status_code != 200:
            console.print(Panel.fit(
                f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                border_style="red",
                title="Error Fetching Addresses"
            ))
            raise click.Abort()
            
        data = response.json()
        addresses = data.get('addresses', [])
        
        output_format = ctx.obj['output']
        
        if output_format == 'json':
            console.print(json.dumps(data, indent=2))
        elif output_format == 'yaml':
            console.print(yaml.dump(data, default_flow_style=False))
        else:
            if not addresses:
                console.print("No addresses found.")
                return
                
            table = Table(title=f"Addresses for Account: {account_id}")
            table.add_column("ID", style="cyan", max_width=20)
            table.add_column("Status", style="green")
            table.add_column("Type", style="blue")
            table.add_column("Address", style="yellow", max_width=30)
            table.add_column("Networks", style="magenta", max_width=40)
            
            for addr in addresses:
                # Truncate long addresses for display
                address_display = addr.get('address', 'N/A')
                if address_display and len(address_display) > 25:
                    address_display = f"{address_display[:10]}...{address_display[-10:]}"
                
                # Join transfer types
                networks = ', '.join(addr.get('transfer_types', []))
                if len(networks) > 35:
                    networks = f"{networks[:32]}..."
                
                table.add_row(
                    addr['id'][:20] + '...' if len(addr['id']) > 20 else addr['id'],
                    addr['status'],
                    addr['type'],
                    address_display,
                    networks
                )
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(addresses)} address(es)[/dim]")
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@addresses.command()
@click.argument('address_id')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.pass_context
def show(ctx, address_id, account):
    """Show address details."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        # Get all addresses and find the specific one
        response = api_client.get(f'/accounts/{account_id}/addresses')
        
        if response.status_code != 200:
            console.print(Panel.fit(
                f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                border_style="red",
                title="Error Fetching Addresses"
            ))
            raise click.Abort()
            
        data = response.json()
        addresses = data.get('addresses', [])
        address = next((addr for addr in addresses if addr['id'] == address_id), None)
        
        if not address:
            console.print(Panel.fit(
                f"[bold red]Address not found[/bold red]\nAddress ID: {address_id}",
                border_style="red",
                title="Not Found"
            ))
            raise click.Abort()
        
        output_format = ctx.obj['output']
        
        if output_format == 'json':
            console.print(json.dumps(address, indent=2))
        elif output_format == 'yaml':
            console.print(yaml.dump(address, default_flow_style=False))
        else:
            table = Table(title=f"Address Details: {address_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("ID", address['id'])
            table.add_row("Status", address['status'])
            table.add_row("Type", address['type'])
            table.add_row("Name", address.get('name') or 'N/A')
            table.add_row("Address", address.get('address') or 'N/A')
            table.add_row("Created", address.get('created', 'N/A'))
            table.add_row("Supported Networks", ', '.join(address.get('transfer_types', [])))
            
            console.print(table)
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

# Transfers commands
@transfers.command()
@click.option('--from', 'source', required=True, type=click.Choice(['wire', 'ach']), help='Source type')
@click.option('--to', 'destination', required=True, help='Destination token (usdc, sbc, etc.)')
@click.option('--network', help='Blockchain network (base, solana, ethereum, etc.)')
@click.option('--amount', required=True, type=float, help='Transfer amount in USD')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.pass_context
def create(ctx, source, destination, network, amount, account):
    """Create a new transfer."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        # Get addresses to find compatible destination
        with Status("[dim]Finding compatible address...", console=console):
            addresses_response = api_client.get(f'/accounts/{account_id}/addresses')
            
            if addresses_response.status_code != 200:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {addresses_response.status_code}: {addresses_response.text}",
                    border_style="red",
                    title="Error Fetching Addresses"
                ))
                raise click.Abort()
            
            addresses_data = addresses_response.json()
            addresses = addresses_data.get('addresses', [])
            
            # Find compatible address
            compatible_address = None
            for addr in addresses:
                if addr['status'] == 'active':
                    transfer_types = addr.get('transfer_types', [])
                    if network and network in transfer_types:
                        compatible_address = addr
                        break
                    elif not network and transfer_types:  # Auto-select if no network specified
                        compatible_address = addr
                        network = transfer_types[0]  # Use first available
                        break
            
            if not compatible_address:
                available_networks = []
                for addr in addresses:
                    if addr['status'] == 'active':
                        available_networks.extend(addr.get('transfer_types', []))
                
                console.print(Panel.fit(
                    f"[bold red]No compatible address found[/bold red]\nRequested network: {network or 'auto'}\nAvailable networks: {', '.join(set(available_networks))}",
                    border_style="red",
                    title="Address Error"
                ))
                raise click.Abort()
        
        # Create transfer request
        transfer_data = {
            "amount": {"value": str(amount), "currency": "USD"},
            "source": {"value_type": "USD", "transfer_type": source},
            "destination": {
                "address_id": compatible_address['id'],
                "value_type": destination.upper(),
                "transfer_type": network
            }
        }
        
        console.print(Panel.fit(
            f"[bold blue]Creating Transfer[/bold blue]\n"
            f"Amount: ${amount} USD\n"
            f"From: {source.upper()}\n"
            f"To: {destination.upper()} on {network}\n"
            f"Address: {compatible_address['id'][:20]}...",
            border_style="blue",
            title="Transfer Details"
        ))
        
        if ctx.obj['output'] in ['json', 'yaml']:
            if ctx.obj['output'] == 'json':
                syntax = Syntax(json.dumps(transfer_data, indent=2), "json", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Request Body"))
            else:
                syntax = Syntax(yaml.dump(transfer_data, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Request Body"))
        
        # Make the API request
        with Status("[bold green]Creating transfer...", console=console):
            import uuid
            transfer_response = api_client.post(
                f'/accounts/{account_id}/transfers',
                headers={"Idempotency-Key": str(uuid.uuid4())},
                json=transfer_data
            )
            
            if transfer_response.status_code not in [200, 201]:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {transfer_response.status_code}: {transfer_response.text}",
                    border_style="red",
                    title="Transfer Creation Failed"
                ))
                raise click.Abort()
        
        result = transfer_response.json()
        
        console.print(Panel.fit(
            f"[bold green]Transfer Created Successfully[/bold green]\n"
            f"Transfer ID: [cyan]{result['id']}[/cyan]\n"
            f"Status: [yellow]{result['status']}[/yellow]",
            border_style="green",
            title="Success"
        ))
        
        # Show wire instructions if available
        if 'wire_instructions' in result:
            wire_info = result['wire_instructions']
            instructions_text = f"""[bold]Wire Transfer Instructions:[/bold]

Bank Name: {wire_info.get('bank_name', 'N/A')}
Account Number: {wire_info.get('account_number', 'N/A')}  
Routing Number: {wire_info.get('routing_number', 'N/A')}
Beneficiary: {wire_info.get('beneficiary_name', 'N/A')}"""
            
            console.print(Panel(
                instructions_text,
                border_style="yellow",
                title="Wire Instructions"
            ))
        
        if ctx.obj['verbose']:
            if ctx.obj['output'] == 'json':
                syntax = Syntax(json.dumps(result, indent=2), "json", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Full Response"))
            elif ctx.obj['output'] == 'yaml':
                syntax = Syntax(yaml.dump(result, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Full Response"))
                
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@transfers.command('list')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.option('--status', help='Filter by status (pending, processing, completed, failed)')
@click.pass_context
def list_transfers(ctx, account, status):
    """List all transfers for an account."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        with Status("[dim]Fetching transfers...", console=console):
            response = api_client.get(f'/accounts/{account_id}/transfers')
            
            if response.status_code != 200:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                    border_style="red",
                    title="Error Fetching Transfers"
                ))
                raise click.Abort()
                
            data = response.json()
            transfers = data.get('transfers', [])
            
            # Filter by status if provided
            if status:
                transfers = [t for t in transfers if t.get('status') == status]
        
        output_format = ctx.obj['output']
        
        if output_format == 'json':
            filtered_data = {'transfers': transfers} if status else data
            syntax = Syntax(json.dumps(filtered_data, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif output_format == 'yaml':
            filtered_data = {'transfers': transfers} if status else data
            syntax = Syntax(yaml.dump(filtered_data, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            if not transfers:
                console.print(Panel.fit(
                    "[dim]No transfers found[/dim]",
                    border_style="yellow"
                ))
                return
                
            table = Table(title=f"Transfers for Account: {account_id}")
            table.add_column("ID", style="cyan", max_width=20)
            table.add_column("Status", style="green")
            table.add_column("Amount", style="yellow")
            table.add_column("From", style="blue")
            table.add_column("To", style="magenta")
            table.add_column("Created", style="dim")
            
            for transfer in transfers:
                # Truncate long IDs for display
                transfer_id = transfer['id']
                if len(transfer_id) > 18:
                    transfer_id = f"{transfer_id[:15]}..."
                
                amount = transfer.get('amount', {})
                amount_str = f"${amount.get('value', 'N/A')} {amount.get('currency', '')}"
                
                source = transfer.get('source', {})
                source_str = f"{source.get('value_type', 'N/A')} ({source.get('transfer_type', 'N/A')})"
                
                dest = transfer.get('destination', {})
                dest_str = f"{dest.get('value_type', 'N/A')} ({dest.get('transfer_type', 'N/A')})"
                
                created = transfer.get('created_at', 'N/A')
                if len(created) > 16:
                    created = created[:16].replace('T', ' ')
                
                table.add_row(
                    transfer_id,
                    transfer['status'],
                    amount_str,
                    source_str,
                    dest_str,
                    created
                )
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(transfers)} transfer(s)[/dim]")
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@transfers.command()
@click.argument('transfer_id')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.pass_context
def show(ctx, transfer_id, account):
    """Show transfer details."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        with Status("[dim]Fetching transfer details...", console=console):
            response = api_client.get(f'/accounts/{account_id}/transfers/{transfer_id}')
            
            if response.status_code != 200:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                    border_style="red",
                    title="Error Fetching Transfer"
                ))
                raise click.Abort()
                
            transfer = response.json()
        
        output_format = ctx.obj['output']
        
        if output_format == 'json':
            syntax = Syntax(json.dumps(transfer, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif output_format == 'yaml':
            syntax = Syntax(yaml.dump(transfer, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            table = Table(title=f"Transfer Details: {transfer_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("ID", transfer['id'])
            table.add_row("Status", transfer['status'])
            
            amount = transfer.get('amount', {})
            table.add_row("Amount", f"${amount.get('value', 'N/A')} {amount.get('currency', '')}")
            
            source = transfer.get('source', {})
            table.add_row("Source", f"{source.get('value_type', 'N/A')} via {source.get('transfer_type', 'N/A')}")
            
            dest = transfer.get('destination', {})
            table.add_row("Destination", f"{dest.get('value_type', 'N/A')} via {dest.get('transfer_type', 'N/A')}")
            table.add_row("Address ID", dest.get('address_id', 'N/A'))
            
            table.add_row("Created", transfer.get('created_at', 'N/A'))
            table.add_row("Updated", transfer.get('updated_at', 'N/A'))
            
            if transfer.get('note'):
                table.add_row("Note", transfer['note'])
            
            console.print(table)
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@transfers.command()
@click.argument('transfer_id')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.pass_context
def instructions(ctx, transfer_id, account):
    """Show wire/ACH instructions for a transfer."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        with Status("[dim]Fetching transfer instructions...", console=console):
            response = api_client.get(f'/accounts/{account_id}/transfers/{transfer_id}')
            
            if response.status_code != 200:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                    border_style="red",
                    title="Error Fetching Transfer"
                ))
                raise click.Abort()
                
            transfer = response.json()
        
        output_format = ctx.obj['output']
        
        # Extract instructions
        wire_instructions = transfer.get('wire_instructions')
        ach_instructions = transfer.get('ach_instructions')
        
        if not wire_instructions and not ach_instructions:
            console.print(Panel.fit(
                "[bold yellow]No payment instructions available[/bold yellow]\nThis transfer may not require manual funding",
                border_style="yellow",
                title="No Instructions"
            ))
            return
        
        if output_format == 'json':
            instructions_data = {}
            if wire_instructions:
                instructions_data['wire_instructions'] = wire_instructions
            if ach_instructions:
                instructions_data['ach_instructions'] = ach_instructions
            syntax = Syntax(json.dumps(instructions_data, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif output_format == 'yaml':
            instructions_data = {}
            if wire_instructions:
                instructions_data['wire_instructions'] = wire_instructions
            if ach_instructions:
                instructions_data['ach_instructions'] = ach_instructions
            syntax = Syntax(yaml.dump(instructions_data, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            if wire_instructions:
                instructions_text = f"""[bold]Wire Transfer Instructions:[/bold]

Bank Name: {wire_instructions.get('bank_name', 'N/A')}
Bank Address: {wire_instructions.get('bank_address', 'N/A')}
Account Number: {wire_instructions.get('account_number', 'N/A')}  
Routing Number: {wire_instructions.get('routing_number', 'N/A')}
Beneficiary Name: {wire_instructions.get('beneficiary_name', 'N/A')}
Beneficiary Address: {wire_instructions.get('beneficiary_address', 'N/A')}"""
                
                if wire_instructions.get('memo'):
                    instructions_text += f"\nMemo: {wire_instructions['memo']}"
                
                console.print(Panel(
                    instructions_text,
                    border_style="blue",
                    title=f"Wire Instructions - Transfer {transfer_id[:20]}..."
                ))
            
            if ach_instructions:
                ach_text = f"""[bold]ACH Transfer Instructions:[/bold]

Account Number: {ach_instructions.get('account_number', 'N/A')}  
Routing Number: {ach_instructions.get('routing_number', 'N/A')}
Account Name: {ach_instructions.get('account_name', 'N/A')}"""
                
                console.print(Panel(
                    ach_text,
                    border_style="green",
                    title=f"ACH Instructions - Transfer {transfer_id[:20]}..."
                ))
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

# Automations commands
@automations.command()
@click.argument('name')
@click.option('--token', required=True, help='Token type (usdc, sbc, etc.)')
@click.option('--network', help='Blockchain network (base, solana, ethereum, etc.)')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.pass_context
def create(ctx, name, token, network, account):
    """Create a new fiat-to-stablecoin automation."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        # Get addresses to find compatible destination
        with Status("[dim]Finding compatible address...", console=console):
            addresses_response = api_client.get(f'/accounts/{account_id}/addresses')
            
            if addresses_response.status_code != 200:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {addresses_response.status_code}: {addresses_response.text}",
                    border_style="red",
                    title="Error Fetching Addresses"
                ))
                raise click.Abort()
            
            addresses_data = addresses_response.json()
            addresses = addresses_data.get('addresses', [])
            
            # Find compatible address
            compatible_address = None
            for addr in addresses:
                if addr['status'] == 'active':
                    transfer_types = addr.get('transfer_types', [])
                    if network and network in transfer_types:
                        compatible_address = addr
                        break
                    elif not network and transfer_types:  # Auto-select if no network specified
                        compatible_address = addr
                        network = transfer_types[0]  # Use first available
                        break
            
            if not compatible_address:
                available_networks = []
                for addr in addresses:
                    if addr['status'] == 'active':
                        available_networks.extend(addr.get('transfer_types', []))
                
                console.print(Panel.fit(
                    f"[bold red]No compatible address found[/bold red]\nRequested network: {network or 'auto'}\nAvailable networks: {', '.join(set(available_networks))}",
                    border_style="red",
                    title="Address Error"
                ))
                raise click.Abort()
        
        # Create automation request
        automation_data = {
            "name": name,
            "type": "USD",
            "destination": {
                "address_id": compatible_address['id'],
                "value_type": token.upper(),
                "transfer_type": network
            }
        }
        
        console.print(Panel.fit(
            f"[bold blue]Creating Automation[/bold blue]\n"
            f"Name: {name}\n"
            f"Token: {token.upper()} on {network}\n"
            f"Address: {compatible_address['id'][:20]}...",
            border_style="blue",
            title="Automation Details"
        ))
        
        if ctx.obj['output'] in ['json', 'yaml']:
            if ctx.obj['output'] == 'json':
                syntax = Syntax(json.dumps(automation_data, indent=2), "json", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Request Body"))
            else:
                syntax = Syntax(yaml.dump(automation_data, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Request Body"))
        
        # Make the API request
        with Status("[bold green]Creating automation...", console=console):
            import uuid
            automation_response = api_client.post(
                f'/accounts/{account_id}/automations',
                headers={"Idempotency-Key": str(uuid.uuid4())},
                json=automation_data
            )
            
            if automation_response.status_code not in [200, 201]:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {automation_response.status_code}: {automation_response.text}",
                    border_style="red",
                    title="Automation Creation Failed"
                ))
                raise click.Abort()
        
        result = automation_response.json()
        
        console.print(Panel.fit(
            f"[bold green]Automation Created Successfully[/bold green]\n"
            f"Automation ID: [cyan]{result['id']}[/cyan]\n"
            f"Status: [yellow]{result['status']}[/yellow]",
            border_style="green",
            title="Success"
        ))
        
        # Show wire instructions if available
        if 'wire_instructions' in result:
            wire_info = result['wire_instructions']
            instructions_text = f"""[bold]Customer Wire Instructions:[/bold]

Bank Name: {wire_info.get('bank_name', 'N/A')}
Account Number: {wire_info.get('account_number', 'N/A')}  
Routing Number: {wire_info.get('routing_number', 'N/A')}
Beneficiary: {wire_info.get('beneficiary_name', 'N/A')}
Memo: {wire_info.get('memo') or 'None'}

[dim]Share these instructions with customers to automatically mint {token.upper()} to your wallet.[/dim]"""
            
            console.print(Panel(
                instructions_text,
                border_style="yellow",
                title="Customer Instructions"
            ))
        
        if ctx.obj['verbose']:
            if ctx.obj['output'] == 'json':
                syntax = Syntax(json.dumps(result, indent=2), "json", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Full Response"))
            elif ctx.obj['output'] == 'yaml':
                syntax = Syntax(yaml.dump(result, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Full Response"))
                
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@automations.command('list')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.option('--status', help='Filter by status (pending, complete, failed)')
@click.pass_context
def list_automations(ctx, account, status):
    """List all automations for an account."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        with Status("[dim]Fetching automations...", console=console):
            response = api_client.get(f'/accounts/{account_id}/automations')
            
            if response.status_code != 200:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                    border_style="red",
                    title="Error Fetching Automations"
                ))
                raise click.Abort()
                
            data = response.json()
            automations = data.get('automations', [])
            
            # Filter by status if provided
            if status:
                automations = [a for a in automations if a.get('status') == status]
        
        output_format = ctx.obj['output']
        
        if output_format == 'json':
            filtered_data = {'automations': automations} if status else data
            syntax = Syntax(json.dumps(filtered_data, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif output_format == 'yaml':
            filtered_data = {'automations': automations} if status else data
            syntax = Syntax(yaml.dump(filtered_data, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            if not automations:
                console.print(Panel.fit(
                    "[dim]No automations found[/dim]",
                    border_style="yellow"
                ))
                return
                
            table = Table(title=f"Automations for Account: {account_id}")
            table.add_column("ID", style="cyan", max_width=20)
            table.add_column("Name", style="blue", max_width=25)
            table.add_column("Status", style="green")
            table.add_column("Token", style="yellow")
            table.add_column("Network", style="magenta")
            table.add_column("Created", style="dim")
            
            for automation in automations:
                # Truncate long IDs and names for display
                auto_id = automation['id']
                if len(auto_id) > 18:
                    auto_id = f"{auto_id[:15]}..."
                
                name = automation.get('name', 'N/A')
                if len(name) > 22:
                    name = f"{name[:19]}..."
                
                dest = automation.get('destination', {})
                token = dest.get('value_type', 'N/A')
                network = dest.get('transfer_type', 'N/A')
                
                created = automation.get('created_at', 'N/A')
                if len(created) > 16:
                    created = created[:16].replace('T', ' ')
                
                table.add_row(
                    auto_id,
                    name,
                    automation['status'],
                    token,
                    network,
                    created
                )
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(automations)} automation(s)[/dim]")
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@automations.command()
@click.argument('automation_id')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.pass_context
def show(ctx, automation_id, account):
    """Show automation details."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        with Status("[dim]Fetching automation details...", console=console):
            response = api_client.get(f'/accounts/{account_id}/automations/{automation_id}')
            
            if response.status_code != 200:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                    border_style="red",
                    title="Error Fetching Automation"
                ))
                raise click.Abort()
                
            automation = response.json()
        
        output_format = ctx.obj['output']
        
        if output_format == 'json':
            syntax = Syntax(json.dumps(automation, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif output_format == 'yaml':
            syntax = Syntax(yaml.dump(automation, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            table = Table(title=f"Automation Details: {automation_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("ID", automation['id'])
            table.add_row("Name", automation.get('name', 'N/A'))
            table.add_row("Status", automation['status'])
            
            dest = automation.get('destination', {})
            table.add_row("Token", dest.get('value_type', 'N/A'))
            table.add_row("Network", dest.get('transfer_type', 'N/A'))
            table.add_row("Address ID", dest.get('address_id', 'N/A'))
            
            if automation.get('created_at'):
                table.add_row("Created", automation['created_at'])
            if automation.get('updated_at'):
                table.add_row("Updated", automation['updated_at'])
            
            console.print(table)
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

@automations.command()
@click.argument('automation_id')
@click.option('--account', help='Account ID (uses default if not specified)')
@click.pass_context
def instructions(ctx, automation_id, account):
    """Show customer wire instructions for an automation."""
    try:
        # Use provided account or default
        account_id = account or brale_config.get_default_account()
        if not account_id:
            console.print(Panel.fit(
                "[bold red]No account specified[/bold red]\nUse [cyan]--account <id>[/cyan] or set default with [cyan]brale config set default_account <id>[/cyan]",
                border_style="red",
                title="Missing Account"
            ))
            raise click.Abort()
        
        with Status("[dim]Fetching automation instructions...", console=console):
            response = api_client.get(f'/accounts/{account_id}/automations/{automation_id}')
            
            if response.status_code != 200:
                console.print(Panel.fit(
                    f"[bold red]API Error[/bold red]\nHTTP {response.status_code}: {response.text}",
                    border_style="red",
                    title="Error Fetching Automation"
                ))
                raise click.Abort()
                
            automation = response.json()
        
        output_format = ctx.obj['output']
        
        # Extract instructions
        wire_instructions = automation.get('wire_instructions')
        
        if not wire_instructions:
            console.print(Panel.fit(
                "[bold yellow]No wire instructions available[/bold yellow]\nThis automation may still be processing",
                border_style="yellow",
                title="No Instructions"
            ))
            return
        
        if output_format == 'json':
            syntax = Syntax(json.dumps({'wire_instructions': wire_instructions}, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif output_format == 'yaml':
            syntax = Syntax(yaml.dump({'wire_instructions': wire_instructions}, default_flow_style=False), "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            dest = automation.get('destination', {})
            token = dest.get('value_type', 'N/A')
            network = dest.get('transfer_type', 'N/A')
            
            instructions_text = f"""[bold]Customer Wire Instructions:[/bold]

Bank Name: {wire_instructions.get('bank_name', 'N/A')}
Bank Address: {wire_instructions.get('bank_address', 'N/A')}
Account Number: {wire_instructions.get('account_number', 'N/A')}  
Routing Number: {wire_instructions.get('routing_number', 'N/A')}
Beneficiary Name: {wire_instructions.get('beneficiary_name', 'N/A')}
Beneficiary Address: {wire_instructions.get('beneficiary_address', 'N/A')}"""
            
            if wire_instructions.get('memo'):
                instructions_text += f"\nMemo: {wire_instructions['memo']}"
            
            instructions_text += f"\n\n[dim]Customers can send wire transfers to these details to automatically mint {token} on {network} to your wallet.[/dim]"
            
            console.print(Panel(
                instructions_text,
                border_style="blue",
                title=f"Customer Instructions - Automation {automation_id[:20]}..."
            ))
            
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error[/bold red]\n{e}",
            border_style="red"
        ))
        raise click.Abort()

if __name__ == '__main__':
    main()