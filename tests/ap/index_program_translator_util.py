import index_drr_pass_util
import ir_tools
import op_index_translator_util
import op_index_template_util

class IndexProgramTranslatorMap:

  def __init__(
    self,
    index_func_unique_id2index_program,
    kernel_arg_translator,
    anchor_iter_var_names,
    anchor_iter_dim_splits
  ):
    self.kernel_arg_translator = kernel_arg_translator
    self.anchor_iter_var_names = anchor_iter_var_names
    self.anchor_iter_dim_splits = anchor_iter_dim_splits
    items = index_func_unique_id2index_program.items()
    self.index_func_unique_id2translator = OrderedDict(
      map(
        lambda i: [items[i][0], self.make_translator(i, items[i][1])],
        range(len(items))
      )
    )
    self.split_index_codegen = op_index_template_util.split_index_codegen

  def get_offset_var_name(
    self,
    index_func_unique_id,
    mut_kernel_arg_id_registry,
    mut_lir_code_gen_ctx
  ):
    translator = self.index_func_unique_id2translator[index_func_unique_id]
    ret = translator.translate(
      mut_kernel_arg_id_registry=mut_kernel_arg_id_registry,
      mut_lir_code_gen_ctx=mut_lir_code_gen_ctx
    )
    return ret.iter_var_names[0]

  def get_ptr_index_by_ir_output(
    self,
    index_func_unique_id,
    axis,
    sections,
    mut_kernel_arg_id_registry,
    mut_lir_code_gen_ctx
  ):
    return self.split_index_codegen.get_split_index(axis=axis, sections=sections)

  def get_ptr_index_by_ir_output(
    self,
    index_func_unique_id,
    axis,
    num,
    shape,
    mut_kernel_arg_id_registry,
    mut_lir_code_gen_ctx
  ):
    return self.split_index_codegen.get_split_index(axis=axis, num=num, shape=shape)

  def get_index_var_names_by_ir_output(
    self,
    index_func_unique_id,
    axis,
    num,
    sections,
    shape,
    mut_kernel_arg_id_registry,
    mut_lir_code_gen_ctx
  ):
    return self.split_index_codegen.get_split_index(axis=axis, num=num, shape) if num != 0 else
           self.split_index_codegen.get_split_index(axis=axis, sections)

  def make_translator(self, program_id, index_program):
    pass_manager = ir_tools.create_pass_manager()
    drr_pass = index_drr_pass_util.InsertReshapeBeforeYieldPass()
    pass_manager.add_pass(ir_tools.create_access_topo_drr_one_step_pass(drr_pass))
    pass_manager.add_pass(ir_tools.create_dce_pass())
    pass_manager.run(index_program)
    return IndexProgramTranslator(
      index_program,
      program_id=program_id,
      kernel_arg_translator=self.kernel_arg_translator,
      index_op_translator_maker=op_index_translator_util.OpIndexTranslatorFactory(),
      anchor_iter_var_names=self.anchor_iter_var_names,
      anchor_iter_dim_splits=self.anchor_iter_dim_splits,
    )


class IndexProgramTranslator:

  def __init__(
    self,
    index_program,
    program_id,
    kernel_arg_translator,
    index_op_translator_maker,
    anchor_iter_var_names,
    anchor_iter_dim_splits
  ):
    self.program_id = program_id
    self.program_property = index_program.copy_to_const_program_data()
    self.kernel_arg_translator = kernel_arg_translator
    self.index_op_translator_maker = index_op_translator_maker
    self.anchor_iter_var_names = anchor_iter_var_names
    self.anchor_iter_dim_splits = anchor_iter_dim_splits
    self.ir_value_index2translated_value = MutableList()
    def PushNone(x):
      self.ir_value_index2translated_value.append(None)
    map(PushNone, self.program_property.values)

  def translate(
    self,
    mut_kernel_arg_id_registry,
    mut_lir_code_gen_ctx,
  ):
    def TranslateOp(op_property):
      self._translate_op(op_property, mut_kernel_arg_id_registry, mut_lir_code_gen_ctx)
    map(TranslateOp, self.program_property.ops)
    return self.ir_value_index2translated_value[-1]

  def _translate_op(self, op_property, mut_kernel_arg_id_registry, mut_lir_code_gen_ctx):
    input_properties=map(self._get_value_property, op_property.input_value_indexes)
    output_properties=map(self._get_value_property, op_property.output_value_indexes)
    print('inputs properties: ', input_properties)
    print('outputs properties: ', output_properties)
    index_op_translator = self.index_op_translator_maker(
      index_program_id=self.program_id,
      op_property=op_property,
      input_properties=map(self._get_value_property, op_property.input_value_indexes),
      output_properties=map(self._get_value_property, op_property.output_value_indexes),
      kernel_arg_translator=self.kernel_arg_translator,
      anchor_iter_var_names=self.anchor_iter_var_names,
      anchor_iter_dim_splits=self.anchor_iter_dim_splits
    )
    inputs = map(self._get_translated_value, op_property.input_value_indexes)
    outputs = index_op_translator(
      inputs,
      mut_kernel_arg_id_registry=mut_kernel_arg_id_registry,
      mut_lir_code_gen_ctx=mut_lir_code_gen_ctx
    )
    map(self._set_translated_value, zip(op_property.output_value_indexes, outputs))
    
  def _get_value_property(self, i):
    return self.program_property.values[i]

  def _get_translated_value(self, i):
    return self.ir_value_index2translated_value[i]

  def _set_translated_value(self, pair):
    self.ir_value_index2translated_value[pair[0]] = pair[1]
