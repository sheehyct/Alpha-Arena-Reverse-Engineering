import fs from "fs";
import Ajv from "ajv";

const schema = JSON.parse(fs.readFileSync(new URL("./schema.json", import.meta.url)));
const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

const file = process.argv[2];
if (!file) {
  console.error("Usage: node validate.js <json-file>");
  process.exit(2);
}

const data = JSON.parse(fs.readFileSync(file, "utf-8"));
const ok = validate(data);
if (!ok) {
  console.error("Validation failed:", validate.errors);
  process.exit(1);
}
console.log("OK");
