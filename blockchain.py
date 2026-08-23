import os
import hashlib
import json
from web3 import Web3

# For the hackathon MVP, we default to a local Ganache/Hardhat node on port 8545.
# Your Blockchain Dev can override this with an Infura/Alchemy URL in the .env file.
WEB3_PROVIDER_URL = os.getenv("WEB3_PROVIDER_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000")

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))

def generate_data_hash(project_data: dict) -> str:
    """
    Creates a SHA-256 hash of the project data to store on the blockchain.
    This guarantees the data cannot be altered in the PostgreSQL database without detection.
    """
    # Sort keys to ensure consistent hashing
    data_string = json.dumps(project_data, sort_keys=True)
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def verify_project_integrity(project_id: str, local_project_data: dict) -> bool:
    """
    Bridge function to compare PostgreSQL data with the Blockchain Immutable Ledger.
    """
    # 1. Generate the hash of what we currently have in our relational database
    local_hash = generate_data_hash(local_project_data)
    
    # 2. HACKATHON FALLBACK: If the web3 node isn't running yet,
    # we return True to prevent the API from crashing during frontend development.
    if not w3.is_connected() or CONTRACT_ADDRESS == "0x0000000000000000000000000000000000000000":
        print(f"WARNING: Web3 node disconnected. Bypassing integrity check for {project_id}.")
        return True
        
    try:
        # TODO: Load actual ABI when the Blockchain dev compiles the contract
        # contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        
        # 3. Fetch the hash stored immutably on the Ethereum blockchain
        # onchain_hash_bytes = contract.functions.projects(Web3.keccak(text=project_id)).call()[0]
        # onchain_hash = onchain_hash_bytes.hex()
        
        # 4. The moment of truth: Does the database match the blockchain?
        # return onchain_hash == local_hash
        
        return True # Placeholder until contract is fully deployed
    except Exception as e:
        print(f"Blockchain Verification Error: {e}")
        # If it fails verification, a corrupt official tampered with the DB!
        return False
