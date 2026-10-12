import ConNF
open Lean Meta
/-! For each auxiliary target (names in /out/aux_targets.txt): module, own kind, parent kind, and
whether its OWN value contains `sorryAx` directly (the hole was abstracted into this aux) or it only
reaches sorry transitively through other constants (stable if the solver does not edit this decl). -/
def kindOf : ConstantInfo → String
  | .defnInfo _ => "def" | .thmInfo _ => "theorem" | .opaqueInfo _ => "opaque"
  | .inductInfo _ => "inductive" | .ctorInfo _ => "ctor" | .recInfo _ => "rec"
  | .axiomInfo _ => "axiom" | .quotInfo _ => "quot"
def hasSorry (e : Expr) : Bool := (e.find? fun x => x.isConstOf ``sorryAx).isSome
#eval show MetaM Unit from do
  let env ← getEnv
  let lines ← IO.FS.lines "/out/aux_targets.txt"
  for l in lines do
    let n := l.trim.toName
    let mod := match env.getModuleIdxFor? n with
      | some i => toString (env.header.moduleNames[i.toNat]!)
      | none => "?"
    let pk := match env.find? n.getPrefix with | some ci => kindOf ci | none => "none"
    match env.find? n with
    | none => IO.println s!"AUXPROBE {n} missing"
    | some ci =>
      let dv := match ci.value? (allowOpaque := true) with | some v => hasSorry v | none => false
      let pdv := match env.find? n.getPrefix with
        | some pc => (match pc.value? (allowOpaque := true) with | some v => hasSorry v | none => false)
        | none => false
      IO.println s!"AUXPROBE {n} module={mod} kind={kindOf ci} parent_kind={pk} own_value_sorry={dv} parent_value_sorry={pdv} type_sorry={hasSorry ci.type}"
