// Control (b): shipped starter with ONLY the analyze() return shape changed to the
// v2-documented interface (array of {level,message}); no analysis is performed.
function analyze(program) {
  return [];
}
function checkSemantics(program) {
  return analyze(program);
}
module.exports = { analyze, checkSemantics };
