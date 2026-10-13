import PFR
open Lean Meta
/-! In-image check for the five scored PFR targets whose printed type shows `autoParam (…) sorry`.
For each name in /out/names.txt: does the TYPE (not the proof) contain `sorryAx`; the raw argument
of every `autoParam` in the type; and the axioms reached from the type's constants alone.
Three synthetic, fully proved controls are declared here first. -/

section
open MeasureTheory
variable {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω := by volume_tac)
/-- same binder style as PFR/WeakPFR.lean (`variable … := by volume_tac`) -/
theorem ebvVarAuto : μ = μ := rfl
end
/-- auto-param written in the theorem's own signature -/
theorem ebvSigAuto {Ω : Type*} [MeasurableSpace Ω] (μ : MeasureTheory.Measure Ω := by volume_tac) :
    μ = μ := rfl
/-- no auto-param -/
theorem ebvPlain {Ω : Type*} [MeasurableSpace Ω] (μ : MeasureTheory.Measure Ω) : μ = μ := rfl

def hasSorry (e : Expr) : Bool := (e.find? fun x => x.isConstOf ``sorryAx).isSome

partial def autoArgs (e : Expr) (acc : Array Expr) : Array Expr :=
  let acc := if e.isAppOfArity ``autoParam 2 then acc.push e.appArg! else acc
  match e with
  | .app f a => autoArgs a (autoArgs f acc)
  | .lam _ t b _ => autoArgs b (autoArgs t acc)
  | .forallE _ t b _ => autoArgs b (autoArgs t acc)
  | .letE _ t v b _ => autoArgs b (autoArgs v (autoArgs t acc))
  | .mdata _ b => autoArgs b acc
  | .proj _ _ b => autoArgs b acc
  | _ => acc

def short (s : String) : String := String.mk (s.toList.take 240)

#eval show MetaM Unit from do
  let env ← getEnv
  let lines ← IO.FS.lines "/out/names.txt"
  for l in lines do
    let n := l.trim.toName
    match env.find? n with
    | none => IO.println s!"EBV {n} missing"
    | some ci =>
      let valSorry := match ci.value? (allowOpaque := true) with | some v => hasSorry v | none => false
      let mut typeAx : Array Name := #[]
      for c in ci.type.getUsedConstants do
        for a in (← collectAxioms c) do
          if !typeAx.contains a then typeAx := typeAx.push a
      let allAx ← collectAxioms n
      IO.println s!"EBV {n} type_sorry={hasSorry ci.type} own_value_sorry={valSorry} type_axioms={typeAx} all_axioms={allAx}"
      for a in autoArgs ci.type #[] do
        IO.println s!"EBV   autoParam_arg sorry={hasSorry a} consts={a.getUsedConstants} raw={short (toString a)}"
      IO.println s!"EBV   pp={short (toString (← ppExpr ci.type))}"
