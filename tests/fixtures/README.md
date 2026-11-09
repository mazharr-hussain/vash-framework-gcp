# Gate 1 Fixtures

Only `pass` samples live here. The `fail` samples are built at run time by the tests inside `tmp_path`, so that the runner's normalisation (removing trailing spaces, adding newlines, rejecting invalid JSON and placeholders) does not accidentally "fix" the failing files before the tests can run.
