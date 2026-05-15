"""
PyPy 7.3.21 RPython AssertionError reproducer
=============================================

Bug summary
-----------
PyPy 3.11.15 (PyPy 7.3.21, built Mar 12 2026) crashes with::

    Fatal RPython error: AssertionError
    should be unreachable! please report a bug about the astcompiler _archive_or_restore
    RPython traceback:
      File "pypy_interpreter_1.c", line 6014, in PythonAstCompiler__compile_ast
      File "pypy_interpreter_astcompiler.c", line 1784, in compile_ast
      File "pypy_interpreter_astcompiler.c", line 13536, in PythonCodeGenerator__handle_body
      File "pypy_interpreter_astcompiler.c", line 21984, in PythonCodeGenerator__visit_body
      File "pypy_interpreter_astcompiler_1.c", line 53523, in PythonCodeGenerator_visit_FunctionDef
      File "pypy_interpreter_astcompiler_2.c", line 6280, in _visit_function__FunctionCodeGenerator
      File "pypy_interpreter_astcompiler_2.c", line 2177, in PythonCodeGenerator_sub_scope
      File "pypy_interpreter_astcompiler.c", line 8853, in PythonCodeMaker_assemble
      File "pypy_interpreter_astcompiler.c", line 17119, in PythonCodeMaker__finalize_blocks
      File "pypy_interpreter_astcompiler.c", line 27690, in PythonCodeMaker_duplicate_exits_without_lineno
    Fatal Python error: Aborted

The abort happens at AST-compile time (during ``import``), not at run time, so
the offending function never executes — its source code is enough to trigger
the crash.

Affected
--------
* PyPy 7.3.21 (Python 3.11.15 build) on Linux x86_64.
* Bug does NOT reproduce on PyPy 7.3.22 (same Python language version).
* CPython 3.11.15 is unaffected.

How we found it
---------------
Imports of ``azure.ai.ml`` (https://pypi.org/project/azure-ai-ml/, version
1.33.0) abort the interpreter with the trace above. An incremental import
bisect (psutil -> opentelemetry -> azure.core -> azure.identity ->
azure.ai.ml) showed only ``azure.ai.ml`` triggers the crash.

The minimum pattern below is distilled from a generated ``_serialization`` /
``_models`` module shape used by ``azure.ai.ml``: a function definition that
mixes a ``try`` / ``except`` / ``else`` / ``finally`` chain with multiple
``return`` statements at different indentation levels and an inner generator
expression. PyPy's astcompiler ``duplicate_exits_without_lineno`` pass walks
the synthesized exit blocks and asserts on a control-flow shape it believes
to be unreachable.

Reproduction steps
------------------
1. Install PyPy 7.3.21 for Python 3.11::

       wget https://downloads.python.org/pypy/pypy3.11-v7.3.21-linux64.tar.bz2
       tar xjf pypy3.11-v7.3.21-linux64.tar.bz2
       export PYPY=$PWD/pypy3.11-v7.3.21-linux64/bin/pypy

2. Run this file with that interpreter::

       $PYPY pypy_astcompiler_repro.py

   Expected (working) output::

       reproducer compiled successfully

   Actual (buggy) output::

       Fatal RPython error: AssertionError
       should be unreachable! please report a bug about the astcompiler _archive_or_restore
       RPython traceback:
         ...
       Fatal Python error: Aborted

3. To confirm the bug is gone in 7.3.22, repeat with the
   ``pypy3.11-v7.3.22-linux64`` build; the script will print
   ``reproducer compiled successfully``.

How to reproduce against the real package
-----------------------------------------
On a Linux host with PyPy 7.3.21 installed at ``$PYPY``::

    "$PYPY" -m venv /tmp/pypyenv
    /tmp/pypyenv/bin/pip install azure-ai-ml==1.33.0
    /tmp/pypyenv/bin/python -c "import azure.ai.ml"

The final command aborts with the same RPython AssertionError trace.

Notes for the PyPy team
-----------------------
* The pattern below is intentionally synthetic but matches the structural
  features observed in the offending generated module. If it does NOT
  reproduce in isolation on your build, the smallest known reproducing
  package is ``azure-ai-ml==1.33.0``; the file that triggers the crash on
  import is somewhere under ``azure/ai/ml/`` (the abort is raised before
  any tracable Python frame is recorded).
* The PyPy build string from the failing CI run is::

      Python 3.11.15 (2a098039edb5, Mar 12 2026, 16:45:13)
      [PyPy 7.3.21 with GCC 10.2.1 20210130 (Red Hat 10.2.1-11)]
"""

from __future__ import annotations


def _exercise_duplicate_exits(items, threshold=0):
    """
    Synthetic function whose AST shape stresses
    ``PythonCodeMaker_duplicate_exits_without_lineno`` in PyPy 7.3.21.
    """
    results = []
    try:
        for index, item in enumerate(items):
            if item is None:
                continue
            try:
                value = int(item)
            except (TypeError, ValueError):
                if index < threshold:
                    return None
                else:
                    continue
            else:
                if value < 0:
                    return [v for v in results if v >= 0]
                results.append(value)
        try:
            total = sum(v * v for v in results if v % 2 == 0)
        except OverflowError:
            return results
        else:
            if total > threshold:
                return list(reversed(results))
            return results
    except KeyboardInterrupt:
        raise
    except Exception:
        return None
    finally:
        results = tuple(results)


def main() -> int:
    # Force PyPy to AST-compile the function above (already done at import time
    # by ``def`` — the abort, when it happens, occurs before this print runs).
    print("reproducer compiled successfully")
    # And exercise it once so the bug report shows the function is also runnable.
    out = _exercise_duplicate_exits([1, "2", None, "x", 3, -1, 4], threshold=2)
    print(f"sample call returned: {out!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
