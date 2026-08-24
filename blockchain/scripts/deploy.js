import hre from "hardhat";
import fs from "fs";
import path from "path";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const TrustLedger = await hre.ethers.getContractFactory("MPLADSTrustLedger");
  const ledger = await TrustLedger.deploy();

  await ledger.waitForDeployment();
  const address = await ledger.getAddress();

  console.log(`MPLADSTrustLedger deployed to: ${address}`);

  const artifactPath = path.join(__dirname, "../artifacts/contracts/MPLADSTrustLedger.sol/MPLADSTrustLedger.json");
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  
  const outputData = {
    address: address,
    abi: artifact.abi
  };

  fs.writeFileSync(
    path.join(__dirname, "../../contract_data.json"),
    JSON.stringify(outputData, null, 2)
  );
  console.log("Contract data exported to contract_data.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
