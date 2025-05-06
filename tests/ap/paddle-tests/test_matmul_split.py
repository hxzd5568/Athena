# Copyright (c) 2025 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from os.path import dirname

sys.path.append(dirname(__file__))

import unittest
import utils

import paddle
from paddle.static import InputSpec
import os
import sys
import numpy as np
from dataclasses import dataclass
import typing as t
import itertools


def matmul_add_relu_split(x, y):
    out = paddle.matmul(x, y)
    relu = paddle.nn.functional.relu(out)
    # a = paddle.slice(out, starts=[0], ends=[32], axes=[0])
    a, b = paddle.split(out, num_or_sections=[32, -1], axis=0)
    return relu, a, b


class CINNSubGraphNet(paddle.nn.Layer):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def forward(self, x, y):
        out = self.fn(x, y)
        return out


class TestAPMatmulBinary(unittest.TestCase):
    """
    Test Pir API + @to_static + CINN.
    """

    def setUp(self):
        paddle.seed(2022)
        self.prepare_data()

    def prepare_data(self):
        self.dtype = "float16"

        self.x_shape = [64, 512, 128]
        self.x = paddle.randn(self.x_shape, dtype=self.dtype)
        self.x.stop_gradient = False

        self.y_shape = [128, 1024]
        self.y = paddle.randn(self.y_shape, dtype=self.dtype)
        self.y.stop_gradient = False
        self.inputs = [self.x, self.y]

        # self.b_shape = [3]
        # self.b = paddle.randn(self.b_shape, dtype=self.dtype)
        # self.b.stop_gradient = False

    def eval_symbolic(self, net, use_cinn, profile):
        input_spec = [
            InputSpec(shape=self.x_shape, dtype=self.dtype),
            InputSpec(shape=self.y_shape, dtype=self.dtype),
            # InputSpec(shape=self.b_shape, dtype=self.dtype),
        ]
        net = utils.apply_to_static(net, use_cinn, input_spec)
        net.eval()
        out = utils.run_with_profile(profile, net, self.x, self.y)
        # for i in range(30):
        #     utils.run_with_profile(profile, net, self.x, self.y)
        # paddle.base.core.nvprof_start()
        # for i in range(100):
        #     utils.run_with_profile(profile, net, self.x, self.y)
        # paddle.base.core.nvprof_stop()
        
        return out
    
    
    def train_symbolic(self, net, use_cinn, profile):
        input_spec = [
            InputSpec(shape=self.x_shape, dtype=self.dtype),
            InputSpec(shape=self.y_shape, dtype=self.dtype),
            # InputSpec(shape=self.b_shape, dtype=self.dtype),
        ]
        net = utils.apply_to_static(net, use_cinn, input_spec)
        out = utils.run_with_profile(profile, net, self.x, self.y)
        return net



    def test_matmul_add_gelu(self):
        profile = False
        net = CINNSubGraphNet(matmul_add_relu_split)
        cinn_outs = self.eval_symbolic(net, use_cinn=True, profile=profile)
        dy_outs = self.eval_symbolic(net, use_cinn=False, profile=profile)
        if not profile:
            for i, (a, b) in enumerate(zip(cinn_outs, dy_outs)):
                print('+++++++')
                print(f'pass... {i} \'th result')
                print('+++++++')
                utils.check_result(self.dtype, a.numpy(), b.numpy())
                # self.cal_rms(a.numpy(), b.numpy())
                # print(a.numpy())
                # print('-----')
                # print(b.numpy())
                
    
    def cal_rms(self, x, y):
        if (hasattr(x, "numpy") and hasattr(y, "numpy")):
            x = x.numpy()
            y = y.numpy()
        diff = np.abs(x - y)
        ams = np.mean(diff)
        rms = np.mean(diff / (np.abs(x) + 1e-8))
        print(f'Absolute mean error is: {ams}, relative mean error is {rms}')

    def notest_matmul_relu_split(self):
        def measure_time(net, num_tests=100):
            flag_num_tests = os.getenv('FLAGS_num_tests')
            if flag_num_tests is not None:
                num_tests = int(flag_num_tests)
            for i in range(30):
                net(*self.inputs)
            # repeat
            paddle.base.core.nvprof_start()
            for i in range(num_tests):
                net(*self.inputs)
            paddle.base.core.nvprof_stop()
        flag_comp_perf = os.getenv('FLAGS_ap_performance')
        if flag_comp_perf is not None and flag_comp_perf == '0':
            net = CINNSubGraphNet(matmul_add_relu_split)
            dy_net = self.train_symbolic(net, use_cinn=False, profile=False)
            measure_time(dy_net)
            paddle.device.cuda.empty_cache()
        else:
            net = CINNSubGraphNet(matmul_add_relu_split)
            ap_net = self.train_symbolic(net, use_cinn=True, profile=False)
            measure_time(ap_net)
            paddle.device.cuda.empty_cache()

if __name__ == "__main__":
    unittest.main()
