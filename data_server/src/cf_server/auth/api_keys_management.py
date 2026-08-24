import argparse
import inspect
from pathlib import Path

import pandas as pd
from datetime import datetime
import secrets
import string

BASE_DIR = Path(__file__).resolve().parent / "keys"
API_KEYS_FILE = BASE_DIR / 'api_keys.csv'
API_KEYS_LOGS_FILE = BASE_DIR / 'api_keys_log_usage.csv'

"""
This Python script provides a straightforward way to manage API keys for the data server. 
It should be executed as follows:
- python api_keys_management.py generate_key --name "Alice" --mail "alice@example.com" --others "team-a"
- python api_keys_management.py deactivate_key --api_key "cf-dataloader-abc123..."
- python api_keys_management.py reactivate_key --api_key "cf-dataloader-abc123..."
"""

"""
This is just a dummy implementation of API keys management 
-> more sophisticated solutions, adapters, etc. must be implemented
"""


def generate_key(name: str, mail: str, others: str) -> str:
    """Generate a new api_key."""

    # load keys file if exists
    if API_KEYS_FILE.exists():
        keys_df = pd.read_csv(API_KEYS_FILE)
    else:
        keys_df = pd.DataFrame(columns=['name', 'mail', 'others', 'creation_date', 'active', 'key'])

    # generate random API keys (128 chars: letters + digits)
    alphabet = string.ascii_letters + string.digits
    api_key = 'cf-dataloader-' + ''.join(secrets.choice(alphabet) for _ in range(64))
    while api_key in keys_df['key'].values:  # duplicate check
        api_key = 'cf-dataloader-' + ''.join(secrets.choice(alphabet) for _ in range(64))

    # save new key entry
    new_row = {
        'name': name,
        'mail': mail,
        'others': others,
        'creation_date': datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        'active': True,
        'key': api_key
    }
    keys_df = pd.concat([keys_df, pd.DataFrame([new_row])], ignore_index=True)
    keys_df.to_csv(API_KEYS_FILE, index=False)
    print(f"API key {api_key[:20]}… has been created.")
    return api_key


def verify_key(api_key: str) -> bool:
    """Check if given api_key exists and is active."""

    if not API_KEYS_FILE.exists():
        return False
    keys_df = pd.read_csv(API_KEYS_FILE)
    return ((keys_df['key'] == api_key) & keys_df['active']).any()


def deactivate_key(api_key: str) -> None:
    """Deactivate key."""

    if not API_KEYS_FILE.exists():
        return False
    keys_df = pd.read_csv(API_KEYS_FILE)
    keys_df.loc[keys_df["key"] == api_key, "active"] = False
    keys_df.to_csv(API_KEYS_FILE, index=False)
    print(f"API key {api_key[:20]}… has been deactivated.")


def reactivate_key(api_key: str) -> None:
    """Reactivate key."""

    if not API_KEYS_FILE.exists():
        return False
    keys_df = pd.read_csv(API_KEYS_FILE)
    keys_df.loc[keys_df["key"] == api_key, "active"] = True
    keys_df.to_csv(API_KEYS_FILE, index=False)
    print(f"API key {api_key[:20]}… has been reactivated.")


# --- CLI ---

FUNCTIONS = {
    'generate_key': generate_key,
    'deactivate_key': deactivate_key,
    'reactivate_key': reactivate_key,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='API Key Manager — call any function by name with its parameters.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
            Examples:
            python api_keys_management.py generate_key --name "Alice" --mail "alice@example.com" --others "team-a"
            python api_keys_management.py deactivate_key --api_key "cf-dataloader-abc123..."
            python api_keys_management.py reactivate_key --api_key "cf-dataloader-abc123..."
        """
    )

    parser.add_argument('function', choices=FUNCTIONS.keys(), help='Function to call')

    # Dynamically add --<param> flags for every function parameter
    # We parse known args first so each function's params can be added after
    args, remaining = parser.parse_known_args()

    fn = FUNCTIONS[args.function]
    sig = inspect.signature(fn)

    for param_name, param in sig.parameters.items():
        has_default = param.default is not inspect.Parameter.empty
        parser.add_argument(
            f'--{param_name}',
            required=not has_default,
            default=param.default if has_default else None,
            help=f'Parameter for {args.function}()',
        )

    args = parser.parse_args()
    kwargs = {
        param_name: getattr(args, param_name)
        for param_name in sig.parameters
    }

    result = fn(**kwargs)

    if result is not None:
        print(result)
