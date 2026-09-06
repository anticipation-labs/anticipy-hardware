# QA fixture package release check

Date: 2026-08-28

| Check | Result | Evidence |
|---|---|---|
| Parametric generation | PASS | 42 printed parts and 26 unique pose keys generated without exception |
| STL solid/manifold check | PASS | 42/42 finite, watertight, consistent, positive-volume, single-body meshes with zero degenerate faces |
| Bambu P2S volume check | PASS | 42/42 parts fit a 256 x 256 x 256 mm axis-aligned build volume |
| Editable geometry | PASS | 42 part STEP files and three assembly-view STEP files |
| Orientation mapping | PASS | Six faces, twelve edges and eight corners; 26/26 keys present |
| Python syntax | PASS | Generator, verifier, audio scorer and acceptance evaluator compiled with Python 3.12 |
| Acceptance evaluator logic | PASS | Numeric pass/fail, text pass and blank/incomplete cases exercised |
| Rattle audio scorer logic | PASS | Synthetic quiet DUT returned 0/PASS and seeded loud impulse returned 1/FAIL |
| Whole-package consistency | PASS | `validate_package.py`: 42 STL, 45 STEP, 26 poses, 47 BOM lines, 59 acceptance tests, zero errors |
| Arduino sketch structure | PASS WITH LIMIT | Pin maps, fail-open inputs, balanced source and fail-off outputs checked; exact-board compilation and bench test remain required |

This report validates the released digital files. It cannot validate print dimensions, solenoid timing, spin, guard containment, acoustic calibration or physical strength before the fixtures exist. Those are deliberately hard gates in `acceptance_test_template.csv`; a real DUT is not allowed into either fixture until the inert-dummy qualification passes.
