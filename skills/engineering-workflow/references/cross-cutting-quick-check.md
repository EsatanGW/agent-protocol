# Cross-Cutting Quick Check

For every non-trivial engineering change, ask:
- Security: does this introduce new trust boundaries, auth, validation, or secret-handling concerns?
- Performance: does this touch hot paths, heavy rendering, large queries, caching, or async work?
- Observability: will someone be able to reconstruct what happened if it fails?
- Testability: can this behavior be reliably verified and repeated?
- Error handling: does this introduce new failure modes that propagate across surfaces (data → API → UI → user → ops)?

If any answer is “yes”, mention it in the plan or review output.
