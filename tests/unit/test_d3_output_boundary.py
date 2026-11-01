"""Fresh synthetic canary for the outer FD capture, never a private identifier."""

import os
import sys

import pytest

from g3_d3_offline_checks import private_streams


def test_raw_fd_and_original_stream_are_contained(capsys):
    marker = b"D3_SYNTHETIC_OUTPUT_BOUNDARY_CANARY\n"
    with capsys.disabled():
        assert os.write(1, marker) == len(marker)
        assert os.write(2, marker) == len(marker)
        sys.__stdout__.write(marker.decode())
        sys.__stdout__.flush()
        sys.__stderr__.write(marker.decode())
        sys.__stderr__.flush()


def test_exception_flushes_original_buffer_before_descriptor_restore(tmp_path, capfd):
    marker = "D3_SYNTHETIC_EXCEPTION_CANARY"
    path = tmp_path / "private-capture.txt"
    with pytest.raises(ValueError, match="SYNTHETIC_FAILURE"):
        with private_streams(path):
            sys.__stdout__.write(marker)
            sys.__stderr__.write(marker)
            raise ValueError("SYNTHETIC_FAILURE")
    captured = capfd.readouterr()
    assert marker not in captured.out + captured.err
    assert path.read_text().count(marker) == 2
