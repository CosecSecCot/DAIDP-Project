const { getDefaultConfig } = require("expo/metro-config");
const { withUniwindConfig } = require("uniwind/metro");

const config = getDefaultConfig(__dirname);

module.exports = withUniwindConfig(config, {
  // relative path to your global.css file
  cssEntryFile: "./global.css",
  dtsFile: "./uniwind-types.d.ts",
});
