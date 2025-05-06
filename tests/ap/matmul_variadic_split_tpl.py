import low_level_ir_code_gen_ctx_util
import kernel_arg_translator_util


def make_kernel_arg_translator():
    return kernel_arg_translator_util.KernelArgTranslator(param_struct_name="args")


def get_anchor_iter_var_names(symbolic_shape):
    return (
        ["coord.batch", "coord.row", "coord.column"]
        if len(symbolic_shape) >= 3
        else ["coord.row", "coord.column"]
    )


def get_anchor_iter_dim_splits(symbolic_shape):
    num_anchor_iters = len(get_anchor_iter_var_names(symbolic_shape))
    diff = len(symbolic_shape) - num_anchor_iters

    def get_dim_split(i):
        # 0 is batch which may have no dimension or multiple dimensions in symbolic_shape
        return diff + 1 if i < num_anchor_iters - 2 else 1

    return map(lambda i: get_dim_split(i), range(num_anchor_iters))


class MatmulVariadicSplitTemplate:
    def __init__(
        self,
        # program_translator,
        mut_kernel_arg_id_registry,
    ):
        # self.program_translator = program_translator
        self.mut_kernel_arg_id_registry = mut_kernel_arg_id_registry
        self.kernel_arg_translator = make_kernel_arg_translator()
        self.dtype2type_name = OrderedDict(
            [
                [PointerType.const_float_ptr, "const float*"],
                [PointerType.const_float16_ptr, "const half*"],
                [PointerType.float_ptr, "float*"],
                [PointerType.float16_ptr, "half*"],
                [DataType.float, "float"],
                [DataType.float16, "half"],
                [DataType.int64_t, "int64_t"],
            ]
        )
        self.input_dim_karg_to_shape_access = MutableOrderedDict()
        self.kernel_name = "MatmulVariadicSplitKernel"
        self.library_name = "matmul_variadic_split_kernel"

    def _register_name(self, pair):
        registry = self.mut_kernel_arg_id_registry
        registry.get_or_create_kernel_arg_id_manul_var_name(
            kernel_arg_id=pair[0], cpp_var_name=pair[1]
        )

    def compile(
        self,
        input0_karg,
        input1_karg,
        output_karg,
        output1_karg,
        output2_karg,
        input0_shape_kargs,
        input1_shape_kargs,
    ):
        kargs_name_pair_list = [
            [input0_karg, "input0"],
            [input1_karg, "input1"],
            [output_karg, "output"],
            [output1_karg, "output1"],
            [output2_karg, "output2"],
            *map(
                lambda i: [input0_shape_kargs[i], f"input0_dim{i}"],
                range(len(input0_shape_kargs)),
            ),
            *map(
                lambda i: [input1_shape_kargs[i], f"input1_dim{i}"],
                range(len(input1_shape_kargs)),
            ),
        ]
        print(f"-- kargs_name_pair_list: {kargs_name_pair_list}")
        map(self._register_name, kargs_name_pair_list)

        # mut_lir_code_gen_ctx = low_level_ir_code_gen_ctx_util.CudaLikeIrCodeGenCtx(
        #     compute_dtype=DataType.float
        # )
        # self.program_translator.translate(
        #     mut_kernel_arg_id_registry=self.mut_kernel_arg_id_registry,
        #     mut_lir_code_gen_ctx=mut_lir_code_gen_ctx,
        # )
        # trivial_code_str = mut_lir_code_gen_ctx.get_stmts_joined_str(indent="    ")
        # print("-- matmul_binary_epilogue_code:\n", trivial_code_str)
        project_module = self.make_project(
            # trivial_code_str,
            input0_karg,
            input1_karg,
            output_karg,
            input0_shape_kargs,
            input1_shape_kargs,
        )
        return CodeGenResult(
            module=project_module,
            kernel_dispatch_func=KernelDispatch,
            kernel_dispatch_const_data=BuiltinSerializableAttrMap(
                kernel_args_getters=self.get_kernel_arg_runtime_getters()
            ),
        )

    def get_kernel_arg_runtime_getters(self):
        all_kernel_arg_id_and_unique_names = (
            self.mut_kernel_arg_id_registry.all_kernel_arg_id2unique_name.items()
        )
        return map(
            lambda pair: pair[0].runtime_getter, all_kernel_arg_id_and_unique_names
        )

    def get_kernel_arg_types(self):
        all_kernel_arg_id_and_unique_names = (
            self.mut_kernel_arg_id_registry.all_kernel_arg_id2unique_name.items()
        )
        print('decl len: ', len(all_kernel_arg_id_and_unique_names))
        print('decl: ', map(lambda pair: pair[0].type, all_kernel_arg_id_and_unique_names))
        return map(lambda pair: pair[0].type, all_kernel_arg_id_and_unique_names)

    def get_kernel_arg_id_var_name(self, kernel_arg_id):
        all_kernel_arg_id2unique_name = (
            self.mut_kernel_arg_id_registry.all_kernel_arg_id2unique_name
        )
        return all_kernel_arg_id2unique_name[kernel_arg_id]

    def get_kernel_arg_list_str(self, for_declare):
        def declare_epilogue_arguments_field(pair):
            kernel_arg_id = pair[0]
            var_name = pair[1]
            field_name = self.kernel_arg_translator.get_param_struct_field_name(
                var_name
            )
            dtype = kernel_arg_id.type
            type_name = self.dtype2type_name[dtype]
            return f"{type_name} {field_name}" if for_declare else f"{field_name}"

        all_kernel_arg_id_and_names = (
            self.mut_kernel_arg_id_registry.all_kernel_arg_id2unique_name.items()
        )
        return ", ".join(
            map(declare_epilogue_arguments_field, all_kernel_arg_id_and_names)
        )

    def get_epilogue_arguments_fields_str(self, indent):
        def declare_epilogue_arguments_field(pair):
            kernel_arg_id = pair[0]
            var_name = pair[1]
            field_name = self.kernel_arg_translator.get_param_struct_field_name(
                var_name
            )
            dtype = kernel_arg_id.type
            type_name = self.dtype2type_name[dtype]
            return f"{type_name} {field_name};"

        generated_kernel_arg_id_and_names = (
            self.mut_kernel_arg_id_registry.generated_kernel_arg_id2unique_name.items()
        )
        return f"\n{indent}".join(
            map(declare_epilogue_arguments_field, generated_kernel_arg_id_and_names)
        )

    def get_epilogue_arguments_init_str(self, param_obj_name, indent):
        def declare_epilogue_arguments_assign(pair):
            kernel_arg_id = pair[0]
            var_name = pair[1]
            field_name = self.kernel_arg_translator.get_param_struct_field_name(
                var_name
            )
            return f"{param_obj_name}.{field_name} = {var_name};"

        generated_kernel_arg_id_and_names = (
            self.mut_kernel_arg_id_registry.generated_kernel_arg_id2unique_name.items()
        )
        return f"\n{indent}".join(
            map(declare_epilogue_arguments_assign, generated_kernel_arg_id_and_names)
        )

    def get_params_input_shape_init_str(self, input_name, input_shape_kargs, indent):
        def init_input_shape_with_args(i):
            def get_creator():
                return f"{input_name}_shape[{i}]"

            karg_var_name = self.get_kernel_arg_id_var_name(input_shape_kargs[i])
            self.input_dim_karg_to_shape_access.get_or_create(
                karg_var_name, get_creator
            )
            return f"{indent}{input_name}_shape[{i}] = {karg_var_name};"

        shape_vector_init_str = (
            f"{input_name}_shape.resize({len(input_shape_kargs)});\n"
        )
        return shape_vector_init_str + "\n".join(
            map(init_input_shape_with_args, range(len(input_shape_kargs)))
        )

    def make_project(
        self,
        # trivial_code_str,
        input0_karg,
        input1_karg,
        output_karg,
        input0_shape_kargs,
        input1_shape_kargs,
    ):
        code_template = """
#include <cuda.h>
#include <cuda_fp16.h>
#include <vector>

#include "cutlass_matmul.cuh"
#include "profile.h"

namespace ap {

template <typename T>
struct SplitEpilogueFunctor {
  struct Arguments {
    int64_t input0_dim0; // Batch size
    int64_t input0_dim1; // Rows of matrix A
    int64_t input1_dim1; // Columns of matrix B
    // half* out_ptr_0;     // Output buffer for the first split part
    // half* out_ptr_1;     // Output buffer for the first split part
    half* split_out_ptrs[2];
  };

  __forceinline__ __host__ __device__
  T operator()(T x, const Arguments& args, const MatrixCoord& coord) const {
    T out;
    int64_t linear_index = coord.batch * args.input0_dim1 * args.input1_dim1 +
                           coord.row * args.input1_dim1 + coord.column;
    float op1_out0 = static_cast<float>(0.000000);
    float op2_out0 = static_cast<float>(((x >= op1_out0) ? (x) : (op1_out0)));
    int64_t ptr_id =  coord.batch / (args.input0_dim0 / 2);
    int64_t ptr_bias = ptr_id * args.input0_dim0 / 2 * args.input0_dim1 * args.input1_dim1;

    args.split_out_ptrs[ptr_id][linear_index - ptr_bias] = static_cast<half>(x);
    
    out = op2_out0;
    return out;
  }
};

template <int TuningConfigId>
static void RunMatmulWithSplitKernel(const GemmEpilogueParams &params, const half* input0, const half* input1, half* output,
                                     int64_t input0_dim0, int64_t input0_dim1, int64_t input0_dim2, int64_t input1_dim1,
                                     half* out_ptr_0, half* out_ptr_1) {
  using ElementT = half;
  using ElementComputeT = float;

  typename SplitEpilogueFunctor<ElementComputeT>::Arguments epilogue_args;

  epilogue_args.input0_dim0 = input0_dim0;
  epilogue_args.input0_dim1 = input0_dim1;
  epilogue_args.input1_dim1 = input1_dim1;
  epilogue_args.split_out_ptrs[0] = out_ptr_0;
  epilogue_args.split_out_ptrs[1] = out_ptr_1;

  constexpr int AlignA = AP_ALIGNMENT_half(128);
  constexpr int AlignB = AP_ALIGNMENT_half(32);

  CutlassMatmulAddVariadic<ElementT, ElementComputeT, SplitEpilogueFunctor,
                           AlignA, AlignB, TuningConfigId>(params,
                                                           epilogue_args);
}

} // namespace ap

extern "C" {

void MatmulVariadicSplitKernel(void* stream_ptr, const half* input0, const half* input1, half* output, half* out_ptr_0, half* out_ptr_1,
                       int64_t input0_dim0, int64_t input0_dim1, int64_t input0_dim2, int64_t input1_dim1) {
  std::vector<int64_t> input0_shape;
  input0_shape.resize(3);
  input0_shape[0] = input0_dim0;
  input0_shape[1] = input0_dim1;
  input0_shape[2] = input0_dim2;

  std::vector<int64_t> input1_shape;
  input1_shape.resize(2);
  input1_shape[0] = input0_dim2;
  input1_shape[1] = input1_dim1;

  cudaStream_t* cuda_stream_ptr = reinterpret_cast<cudaStream_t*>(stream_ptr);
  ap::GemmEpilogueParams params(
      *cuda_stream_ptr, input0, input1, nullptr, output, input0_shape, input1_shape, std::vector<int64_t>{});


#if AP_ENABLE_AUTOTUNE
  AP_AUTOTUNE_half(ap::RunMatmulWithSplitKernel, *cuda_stream_ptr, params, input0, input1, output,
                   input0_dim0, input0_dim1, input0_dim2, input1_dim1, out_ptr_0, out_ptr_1);
#else
  ap::RunMatmulWithSplitKernel<ap::DefaultConfig::kConfigId>(params, input0, input1, output,
                                                             input0_dim0, input0_dim1, input0_dim2, input1_dim1,
                                                             out_ptr_0, out_ptr_1);
#endif
}
} 
  """

        code = code_template
        print('code is: ', code)
        source_dir = "/work/Athena/tests/ap/matmul"
        cutlass_dir = "/work/Athena/tests/ap/matmul/cutlass"
        compile_cmd = (
            "nvcc -std=c++17 -O3 -Xcompiler=-fPIC -arch=sm_80 --expt-relaxed-constexpr"
        )
        compile_cmd = compile_cmd + " -I " + cutlass_dir + "/include"
        compile_cmd = compile_cmd + " -I " + cutlass_dir + "/tools/util/include"
        compile_cmd = compile_cmd + " -I " + source_dir
        compile_cmd = (
            compile_cmd
            + " -DCUTLASS_ENABLE_TENSOR_CORE_MMA=1 -DCUTLASS_DEBUG_TRACE_LEVEL=0"
        )
        compile_cmd = compile_cmd + " -DAP_ENABLE_AUTOTUNE=1 -DAP_ENABLE_DEBUG=0"
        compile_cmd = (
            compile_cmd
            + f" --shared {self.library_name}.cu -o lib{self.library_name}.so"
        )

        return CodeModule(
            FuncDeclare(
                DataType.void,
                self.kernel_name,
                [PointerType.void_ptr, *self.get_kernel_arg_types()],
            ),
            Project(
                nested_files=Project.Directory(
                    [f"{self.library_name}.cu", Project.FileContent(code)],
                    ["make.sh", Project.FileContent(compile_cmd)],
                ),
                compile_cmd="sh make.sh",
                so_relative_path=f"lib{self.library_name}.so",
            ),
        )


def KernelDispatch(ctx):
    so_func = ctx.get_so_function("MatmulVariadicSplitKernel")
    stream_ptr = ctx.device_ctx.get_stream_addr_as_void_ptr()
    getters = ctx.kernel_dispatch_const_data.kernel_args_getters
    args = [stream_ptr, *map(lambda getter: getter(ctx), getters)]
    margs = MutableList()
    apply(so_func, args)
