"""
ARC-20 Token Creation for StreamFi
Hackathon Requirement: Demonstrate ARC standard usage
"""

from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
import json

# TestNet Configuration
ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"  # Public Algonode TestNet RPC endpoint
ALGOD_TOKEN = ""  # No token required for the public Algonode endpoint (left blank)

# Your deployer mnemonic (used to derive the private key that will create the asset)
DEPLOYER_MNEMONIC = "cluster coin olympic congress ribbon lamp despair maple dizzy disagree undo inquiry purchase hamster curve nuclear topic shaft evil glide loud soldier talk absent wool"

def create_arc20_token():
    """
    Create ARC-20 compliant fungible token for StreamFi.

    This function:
    - Initializes an Algod client to communicate with the TestNet node.
    - Derives the deployer's private key and address from the mnemonic.
    - Verifies the deployer has sufficient ALGO to cover creation fees.
    - Builds an AssetConfigTxn with ARC-20-like parameters (decimals, manager/reserve/freeze/clawback).
    - Signs, sends, waits for confirmation, and extracts the created asset ID.
    - Persists token metadata to a local JSON file for later use.
    """
    
    try:
        # Initialize Algod client to talk to the Algorand TestNet via Algonode
        algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
        
        # Convert mnemonic phrase into a private key for transaction signing
        private_key = mnemonic.to_private_key(DEPLOYER_MNEMONIC)
        # Derive the public address corresponding to the private key
        creator_address = account.address_from_private_key(private_key)
        
        # Informational print so the operator knows which address is creating the asset
        print(f" Creator Address: {creator_address}")
        
        # Check the creator's ALGO balance to ensure there are enough funds to create an asset
        # account_info returns microAlgos, divide by 1_000_000 to get ALGO
        account_info = algod_client.account_info(creator_address)
        balance = account_info.get('amount') / 1_000_000
        print(f" Balance: {balance} ALGO")
        
        # Require at least 0.5 ALGO for asset creation (cover fees + minimum balance)
        if balance < 0.5:
            print(" Insufficient balance! Need at least 0.5 ALGO for token creation.")
            print("   Fund your account at: https://bank.testnet.algorand.network/")
            return None
        
        # Get current suggested transaction parameters (fee, first/last valid rounds, genesis hash)
        params = algod_client.suggested_params()
        
        # ARC-20 Token Configuration dictionary.
        # Note: `total` here is specified in base units (taking decimals into account).
        token_config = {
            "total": 1_000_000 * 100,  # Total supply in base units (1,000,000 tokens * 100 because decimals=2)
            "decimals": 2,              # Number of decimal places for the token
            "default_frozen": False,    # Whether new accounts are frozen by default
            "unit_name": "STRM",        # Asset unit/name (ticker)
            "asset_name": "StreamFi Payment Token",  # Human-friendly asset name
            "url": "https://streamfi.algorand.network/token",  # Optional metadata URL
            # Manager, reserve, freeze, and clawback are all set to the creator for demo purposes
            "manager": creator_address,   # Account that can reconfigure the asset
            "reserve": creator_address,   # Holds uncirculated tokens (supply control)
            "freeze": creator_address,    # Can freeze token transfers for an account
            "clawback": creator_address   # Can claw back tokens from accounts
        }
        
        # Print token metadata to provide operator feedback before submission
        print(f"\n Creating ARC-20 Token:")
        print(f"   Name: {token_config['asset_name']}")
        print(f"   Unit: {token_config['unit_name']}")
        # Convert total supply from base units back to human tokens for display
        print(f"   Total Supply: {token_config['total'] / 100:,.0f} STRM")
        print(f"   Decimals: {token_config['decimals']}")
        
        # Build the AssetConfigTxn which will create the ASA on-chain
        # sender: creator address
        # sp: suggested transaction parameters (fees, valid rounds, etc.)
        # other fields are unpacked from token_config
        txn = AssetConfigTxn(
            sender=creator_address,
            sp=params,
            **token_config
        )
        
        # Sign the transaction with the deployer's private key
        signed_txn = txn.sign(private_key)
        
        # Submit the signed transaction to the Algorand network
        print("\n Submitting transaction to TestNet...")
        txid = algod_client.send_transaction(signed_txn)
        print(f"   Transaction ID: {txid}")
        
        # Wait for the transaction to be confirmed in a block (blocking call)
        print(" Waiting for confirmation...")
        wait_for_confirmation(algod_client, txid, 4)
        
        # Retrieve pending transaction info to extract the created asset id
        ptx = algod_client.pending_transaction_info(txid)
        asset_id = ptx["asset-index"]  # The new asset ID assigned by the network
        
        # Success feedback with asset ID and an explorer link for quick verification
        print(f"\n SUCCESS! ARC-20 Token Created!")
        print(f"   Asset ID: {asset_id}")
        print(f"   Explorer: https://testnet.explorer.perawallet.app/asset/{asset_id}")
        
        # Save token metadata to a local JSON file for later reference or automation
        token_info = {
            "asset_id": asset_id,
            "asset_name": token_config["asset_name"],
            "unit_name": token_config["unit_name"],
            "total_supply": token_config["total"],
            "decimals": token_config["decimals"],
            "creator": creator_address,
            "txid": txid
        }
        
        with open("arc20_token_info.json", "w") as f:
            # Write a human-readable JSON file with indentation
            json.dump(token_info, f, indent=2)
        
        print("\n Token info saved to: arc20_token_info.json")
        
        return asset_id
        
    except Exception as e:
        # Catch-all error reporting so the operator sees the failure reason
        print(f"\n Error creating token: {e}")
        return None

if __name__ == "__main__":
    # Startup banner to clearly indicate the script's purpose when run directly
    print("=" * 60)
    print(" StreamFi ARC-20 Token Creator")
    print("   Hackathon Compliance: ARC Standard Implementation")
    print("=" * 60 + "\n")
    
    # Call the function to create the token and capture the returned asset id
    asset_id = create_arc20_token()
    
    # If creation succeeded, print helpful next-step instructions for the operator
    if asset_id:
        print("\n" + "=" * 60)
        print("Token creation complete!")
        print("   Use this Asset ID in your smart contract")
        print("=" * 60)
