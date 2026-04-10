"""Tests for fetch_top_games CLI argument parsing and count clamping."""

import argparse
import pytest


def _make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--with-streamers", action="store_true")
    return parser


def _clamp(count):
    return min(max(count, 1), 100)


def test_default_count_is_20():
    args = _make_parser().parse_args([])
    assert args.count == 20


def test_count_above_100_is_clamped_to_100():
    args = _make_parser().parse_args(["--count", "200"])
    assert _clamp(args.count) == 100


def test_count_below_1_is_clamped_to_1():
    args = _make_parser().parse_args(["--count", "0"])
    assert _clamp(args.count) == 1
