import Analysis
open Lean Meta
/-! For each baseline aux target (names on stdin file), print module, aux kind, parent kind. -/
def kindOf : ConstantInfo → String
  | .defnInfo _ => "def" | .thmInfo _ => "theorem" | .opaqueInfo _ => "opaque"
  | .inductInfo _ => "inductive" | .ctorInfo _ => "ctor" | .recInfo _ => "rec"
  | .axiomInfo _ => "axiom" | .quotInfo _ => "quot"
#eval show MetaM Unit from do
  let env ← getEnv
  let lines ← IO.FS.lines "/ebv/aux_targets.txt"
  for l in lines do
    let n := l.toName
    let mod := match env.getModuleIdxFor? n with
      | some i => toString (env.header.moduleNames[i.toNat]!)
      | none => "?"
    let parent := n.getPrefix
    let pk := match env.find? parent with | some ci => kindOf ci | none => "none"
    IO.println s!"AUXMOD {n} module={mod} parent_kind={pk}"
