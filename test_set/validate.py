from . import utils
import argparse
import importlib.util
import inspect
from pathlib import Path
from typing import Type, Any
import sys
import hashlib
from contextlib import contextmanager
from collections import ChainMap
import numpy as np


def load_class_from_file(file_path: str, class_name: str):
    spec = importlib.util.spec_from_file_location("unnamed", file_path)
    unnamed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(unnamed)
    model_class = getattr(unnamed, class_name, None)
    return model_class


def _get_sha_hash(content):
    m = hashlib.sha256()
    m.update(content.encode())
    return m.hexdigest()


def _save_to_model_path(dump_dir, hash_text):
    file_path = f"{dump_dir}/graph_hash.txt"
    with open(file_path, "w") as f:
        f.write(hash_text)


@contextmanager
def _dump_graph_hash_key_ctx(cmd_args):
    if not cmd_args.dump_graph_hash_key:
        yield {}
        return
    mut_graph_codes = []
    extractor_kwarg = {
        "placeholder_auto_rename": True,
        "mut_graph_codes": mut_graph_codes,
    }
    yield extractor_kwarg
    if len(mut_graph_codes) > 0:
        assert len(mut_graph_codes) == 1, f"{len(mut_graph_codes)=}"
        _save_to_model_path(cmd_args.model_path, _get_sha_hash(mut_graph_codes[0]))


def main(args):
    # with _dump_graph_hash_key_ctx(args) as dump_graph_options:
        model_path = args.model_path
        model_class = load_class_from_file(
            f"{model_path}/model.py", class_name="GraphModule"
        )
        assert model_class is not None
        model = model_class()
        print(f"{model_path=}")

        inputs_params = utils.load_converted_from_text(f"{model_path}")
        params = inputs_params["weight_info"]
        inputs = inputs_params['input_info']

        # params = dict(ChainMap(params, inputs))
        params.update(inputs)
        state_dict = {k: utils.replay_tensor(v) for k, v in params.items()}
        

        y = model(**state_dict)[0]

        print(np.argmin(y), np.argmax(y))
        print(y.shape)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="load and run model")
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to folder e.g '../test_dataset'",
    )
    args = parser.parse_args()
    main(args=args)
