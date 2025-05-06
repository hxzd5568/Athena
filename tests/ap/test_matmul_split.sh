#!/bin/bash

export CUDA_VISIBLE_DEVICES="3"
export NVIDIA_TF32_OVERRIDE=0

sh make_axpr.sh

# AP specific settings
export FLAGS_enable_ap=1
export AP_WORKSPACE_DIR=$(pwd)/ap_workspace
export AP_PATH=$(pwd)/

# CINN related settings
export FLAGS_check_infer_symbolic=1
export FLAGS_enable_pir_api=1
export FLAGS_cinn_bucket_compile=True
export FLAGS_prim_enable_dynamic=True
export FLAGS_prim_all=false
export FLAGS_pir_apply_shape_optimization_pass=1
export FLAGS_group_schedule_tiling_first=1
export FLAGS_cinn_new_group_scheduler=1
# export GLOG_v=8
# export FLAGS_ap_performance=1
# export GLOG_vmodule=ap_generic_drr_pass=6

nsys_args="nsys profile --stats true -w true -t cuda,nvtx,osrt,cudnn,cublas \
    --capture-range=cudaProfilerApi\
    --force-overwrite true"
     
# /work/Paddle/paddle/ap/src/paddle/pass/ap_generic_drr_pass.cc  cinn_group_cluster_pass  /work/Paddle/paddle/ap/src/paddle/pass/ir_helper_method_class.cc
${nsys_args} python $(pwd)/paddle-tests/test_matmul_split.py
